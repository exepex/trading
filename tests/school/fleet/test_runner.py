"""Story MS-P1j: the fleet runner on a's fakes (one open road, four closed; two sessions)."""

import time
from dataclasses import replace
from datetime import timedelta

import pytest

from fno.school.constants import (
    ROAD_DETAIL_INPUT,
    SLOT_1500,
    ClosureReason,
    ExitReason,
    Outcome,
    RecordKind,  # fmt: skip
    RefusalReason,
    RoadCode,
    UnavailableReason,
)
from fno.school.contracts.accounts import SettlementPrice
from fno.school.contracts.fleet import RunMode
from fno.school.contracts.records import DecisionRecord, ExitRecord, OutcomeRecord
from fno.school.contracts.roads import ROADS
from fno.school.fakes import FakeDriver, FakeMaxLossLaw
from fno.school.fleet.records import ERROR_INPUT
from tests.school.contracts import builders as b
from tests.school.contracts import conformance as c
from tests.school.fleet.rig import DAY2, OPEN_ROAD, Rig

CS1, N0 = b.card("CS1"), b.card("N0")


def trader(**kwargs) -> FakeDriver:
    return FakeDriver(CS1, b.put_spread(), **kwargs)


def records(rig: Rig, session, kind=RecordKind.DECISIONS):
    seal = rig.dashcam.find(session, SLOT_1500, kind)
    return () if seal is None else rig.dashcam.read(seal)


def decision_of(rig: Rig, session, road=OPEN_ROAD, driver="CS1@1") -> DecisionRecord:
    return next(r for r in records(rig, session) if isinstance(r, DecisionRecord) and r.road == road
                and r.decision.driver_id == driver)  # fmt: skip


def test_off_prints_the_school_off_line_and_writes_nothing(tmp_path):
    rig = Rig(tmp_path, (trader(),), enabled=False)
    c.check_fleet_off(rig.fleet, b.SESSION)
    assert rig.dashcam.files == {} and rig.accounts.ledgers == {} and not any(tmp_path.iterdir())


def test_the_fleet_conforms(tmp_path):
    rig = Rig(tmp_path, (trader(), FakeDriver(N0)), (FakeMaxLossLaw(10_000),))
    c.check_fleet(rig.fleet, b.SESSION, {(r.code, d) for r in ROADS for d in ("CS1@1", "N0@1")})
    assert len(rig.accounts.ledgers["CS1@1"]) == 1


def test_a_closed_road_is_sealed_for_every_driver_with_its_reason_and_detail(tmp_path):
    rig = Rig(tmp_path, (trader(),), (FakeMaxLossLaw(10_000),))
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    closed = decision_of(rig, b.SESSION, RoadCode.NIFTY_MONTHLY)
    assert (closed.decision.outcome, closed.decision.reason) == (Outcome.ROAD_CLOSED, ClosureReason.CAPTURE_MISSING)
    assert closed.inputs[ROAD_DETAIL_INPUT] == "no canonical marker"


class Broken(FakeDriver):
    def decide(self, *args):
        raise KeyError("CE 54800 at 412.5")  # a message with a contract and a price: never recorded


class Slow(FakeDriver):
    def decide(self, *args):
        time.sleep(1.0)
        return super().decide(*args)


def test_a_failing_driver_is_sealed_unavailable_by_class_and_the_others_go_on(tmp_path):
    rig = Rig(tmp_path, (Broken(N0), trader()), (FakeMaxLossLaw(10_000),))
    run = rig.fleet.run(b.SESSION, RunMode.REPLAY)
    broken = decision_of(rig, b.SESSION, driver="N0@1")
    assert (broken.decision.outcome, broken.decision.reason) == (Outcome.UNAVAILABLE, UnavailableReason.DRIVER_ERROR)
    assert broken.inputs[ERROR_INPUT] == "KeyError" and "54800" not in broken.to_bytes().decode()
    assert decision_of(rig, b.SESSION).decision.outcome == Outcome.TRADE and len(run.fills) == 1


def test_a_driver_past_its_time_limit_is_sealed_deadline(tmp_path):
    rig = Rig(tmp_path, (Slow(CS1, b.put_spread()),), (FakeMaxLossLaw(10_000),), seconds=0.05)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    late = decision_of(rig, b.SESSION)
    assert (late.decision.outcome, late.decision.reason) == (Outcome.UNAVAILABLE, UnavailableReason.DEADLINE)
    assert rig.accounts.ledgers == {}


def test_a_refused_trade_is_sealed_with_its_law_results_and_never_fills(tmp_path):
    rig = Rig(tmp_path, (trader(),), (FakeMaxLossLaw(1_000),))
    run = rig.fleet.run(b.SESSION, RunMode.REPLAY)
    refused = decision_of(rig, b.SESSION)
    assert (refused.decision.outcome, refused.decision.reason) == (Outcome.REFUSED, RefusalReason.MAX_LOSS)
    assert refused.law_results and run.fills == () and rig.accounts.ledgers == {}


def test_the_card_s_exit_closes_on_a_later_session_and_its_outcome_is_sealed(tmp_path):
    rig = Rig(tmp_path, (trader(),), (FakeMaxLossLaw(10_000),))
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    rig.fleet.drivers = (trader(exit_reason=ExitReason.PROFIT_TARGET),)
    rig.at(DAY2).fleet.run(DAY2, RunMode.REPLAY)
    exits = [r for r in records(rig, DAY2) if isinstance(r, ExitRecord)]
    assert [(e.position_id, e.exit_reason) for e in exits] == [
        (f"CS1@1:{OPEN_ROAD}:{b.SESSION}", ExitReason.PROFIT_TARGET)
    ]
    [outcome] = records(rig, DAY2, RecordKind.OUTCOMES)
    assert (
        isinstance(outcome, OutcomeRecord) and not outcome.is_ticket and outcome.exit_reason == ExitReason.PROFIT_TARGET
    )
    assert outcome.slippage_vs_mid == pytest.approx(4 * 0.5 * 30)  # four legs at half a rupee from the mid, 30 units


def test_a_position_of_another_driver_makes_the_driver_unavailable_never_an_exit(tmp_path):
    rig = Rig(tmp_path, (trader(),), (FakeMaxLossLaw(10_000),))
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    stray = rig.accounts.ledgers["CS1@1"][0]
    rig.accounts.ledgers["CS1@1"] = [replace(stray, position=replace(stray.position, driver_id="DB1@1"))]
    rig.fleet.drivers = (trader(exit_reason=ExitReason.PROFIT_TARGET),)
    rig.at(DAY2).fleet.run(DAY2, RunMode.REPLAY)
    assert decision_of(rig, DAY2).decision.reason == UnavailableReason.DRIVER_ERROR
    assert not [r for r in records(rig, DAY2) if isinstance(r, ExitRecord)]


def test_an_expired_position_settles_before_the_session_s_view_and_its_outcome_is_sealed(tmp_path):
    rig = Rig(tmp_path, (trader(),), (FakeMaxLossLaw(10_000),),
              settlements={("BANKNIFTY", b.EXPIRY): SettlementPrice(1_050.0, "ee" * 32)})  # fmt: skip
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    later = b.EXPIRY + timedelta(days=1)
    rig.snapshots[(OPEN_ROAD, later)] = replace(b.snapshot(), session=later)
    rig.fleet.catalogue.days[later] = tuple(replace(d, session=later) for d in rig.fleet.catalogue.days[b.SESSION])
    rig.fleet.drivers = (FakeDriver(CS1),)
    rig.at(later).fleet.run(later, RunMode.REPLAY)
    exits = [r for r in records(rig, later) if isinstance(r, ExitRecord)]
    assert [e.exit_reason for e in exits] == [ExitReason.EXPIRY]
    [outcome] = records(rig, later, RecordKind.OUTCOMES)
    assert outcome.exit_reason == ExitReason.EXPIRY and outcome.exit.rests_on == "ee" * 32
