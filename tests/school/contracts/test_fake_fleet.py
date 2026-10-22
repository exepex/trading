"""Judge 479 finding 4: the fleet contract and its fake, for MS-P1i's harness; MS-P1j's real fleet passes the same
checks. Also criterion 6: with the switch off the fleet prints the school-off line and records nothing."""

import dataclasses
from datetime import timedelta

import pytest

from fno.school.constants import SCHOOL_OFF_LINE, ClosureReason, Outcome, RefusalReason, RoadCode
from fno.school.contracts.clock import FixedClock
from fno.school.contracts.fleet import RunMode, SessionRun
from fno.school.contracts.roads import ROADS, RoadStatus
from fno.school.fake_fleet import FakeFleet
from fno.school.fakes import (
    FakeAccounts,
    FakeDashcam,
    FakeDriver,
    FakeFills,
    FakeMaxLossLaw,
    FakeRoadCatalogue,
    FakeSnapshotSource,
)
from tests.school.contracts import builders as b
from tests.school.contracts import conformance as c

AT = b.SLOT_AT + timedelta(minutes=4)
CLOSED = RoadStatus(ClosureReason.HASH_MISMATCH)


def every_road(code: str):
    return dataclasses.replace(b.card(code), roads=tuple(r.code for r in ROADS))


def fleet(enabled: bool = True, limit: float = 10_000, dashcam: FakeDashcam | None = None) -> FakeFleet:
    days = tuple(b.road_day(r.code) if r.code == RoadCode.BANKNIFTY_MONTHLY else b.road_day(r.code, CLOSED)
                 for r in ROADS)  # fmt: skip
    snapshots = FakeSnapshotSource({(RoadCode.BANKNIFTY_MONTHLY, b.SESSION): b.snapshot()})
    drivers = (FakeDriver(every_road("CS1"), b.put_spread()), FakeDriver(every_road("N0")))
    return FakeFleet(enabled, FakeRoadCatalogue({b.SESSION: days}), snapshots, drivers, (FakeMaxLossLaw(limit),),
                     FakeAccounts(2_000_000), FakeFills(), dashcam or FakeDashcam(), FixedClock(AT))  # fmt: skip


def test_the_fake_fleet_conforms():
    scheduled = {(r.code, d) for r in ROADS for d in ("CS1@1", "N0@1")}
    runner = fleet()
    c.check_fleet(runner, b.SESSION, scheduled)
    assert runner.accounts.view("CS1@1", {}, b.SESSION).open_positions, "the one open road's trade filled"


def test_off_the_fleet_records_nothing():
    c.check_fleet_off(fleet(enabled=False), b.SESSION)


def test_closed_roads_and_refusals_are_sealed_decisions():
    run = fleet(limit=1_000).run(b.SESSION, RunMode.REPLAY)
    outcomes = {(r.road, r.decision.driver_id): (r.decision.outcome, r.decision.reason) for r in run.decisions}
    assert outcomes[(RoadCode.NIFTY_MONTHLY, "CS1@1")] == (Outcome.ROAD_CLOSED, ClosureReason.HASH_MISMATCH)
    assert outcomes[(RoadCode.BANKNIFTY_MONTHLY, "CS1@1")] == (Outcome.REFUSED, RefusalReason.MAX_LOSS)
    assert run.fills == ()


def test_a_trading_day_without_roads_seals_nothing():
    run = fleet().run(b.SESSION + timedelta(days=5), RunMode.REPLAY)
    assert run.decisions == () and run.decisions_seal is None


def test_a_session_run_is_consistent():
    with pytest.raises(ValueError):
        SessionRun(b.SESSION, RunMode.RECORD, SCHOOL_OFF_LINE, fills=(b.filled(),))
    with pytest.raises(ValueError):
        SessionRun(b.SESSION, RunMode.RECORD, "", decisions=(object(),))  # decisions without their seal
