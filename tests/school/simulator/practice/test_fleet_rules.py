"""The practice fleet's rules (MS-SIM-d2): AI drivers, the live refusal, separation, the data spend, dated STT."""

from dataclasses import replace
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from fno.config import ROOT
from fno.costs import order_charges
from fno.research_data.calendar import CsvSessionCalendar
from fno.school.constants import ClosureReason, RoadCode
from fno.school.contracts.fleet import RunMode
from fno.school.execution import practice_wiring
from fno.school.execution.quote_rules import LIVE
from fno.school.fakes import FakeSettlementSource
from fno.school.simulator.constants import PracticeRefusal
from fno.school.simulator.practice.drivers import AiDriverNotSimulated, simulable
from fno.school.simulator.practice.fleet import HomeUnderThePilot, PracticeParts, build_practice_fleet
from fno.school.simulator.spreads.model import Scenario, SpreadModel
from fno.school.simulator.windows import PracticeWindows
from tests.school.safety.law_builders import FixedMargin
from tests.school.simulator.practice import test_fleet as tf
from tests.school.simulator.source import builders as sb

CALENDAR_2023 = CsvSessionCalendar(
    "date,kind,description,source_url\n2022-01-26,holiday,t,https://example.test/c\n"
    "2023-01-26,holiday,t,https://example.test/c\n"
)
MONTHLIES_2023, WEEKLIES_2023 = (date(2023, 4, 27), date(2023, 5, 25)), (date(2023, 4, 6), date(2023, 4, 13))


@pytest.fixture(autouse=True)
def archive_stubbed(monkeypatch):
    monkeypatch.setattr(practice_wiring, "build_settlement_source", lambda: FakeSettlementSource({}))


def driver(role: str, family: str = "capped_seller"):
    return SimpleNamespace(card=SimpleNamespace(role=role, family=family, driver_id=f"X_{role}@v1"))


def test_an_ai_card_is_refused_by_name_and_nothing_is_dropped_silently():
    assert simulable([driver("rule"), driver("control", "nothing")]) != ()
    with pytest.raises(AiDriverNotSimulated, match="ai_driver_not_simulated") as raised:
        simulable([driver("rule"), driver("ai", "ai")])
    assert raised.value.reason is PracticeRefusal.AI_DRIVER_NOT_SIMULATED


def test_an_ai_family_card_is_refused_even_with_a_rule_role():
    with pytest.raises(AiDriverNotSimulated):
        simulable([driver("rule", "ai")])


def test_the_practice_fleet_refuses_an_ai_card_when_it_is_built(tmp_path, monkeypatch):
    from fno.school.simulator.practice import fleet as practice_fleet

    monkeypatch.setattr(practice_fleet, "build_school_drivers", lambda cfg, root: (driver("ai", "ai"),))
    with pytest.raises(AiDriverNotSimulated, match="ai_driver_not_simulated"):
        tf.fleet(tmp_path)


def test_without_the_practice_rules_the_live_fleet_closes_every_road_on_these_quotes(tmp_path):
    """Criterion 12: the same fleet under LIVE rules refuses the unmeasured quotes; no trade, no fill."""
    live = replace(tf.fleet(tmp_path), rules=LIVE)
    run = live.run(tf.sb.SESSION, RunMode.REPLAY)
    reasons = {r.road_closed_by for r in run.decisions}
    assert reasons == {ClosureReason.SIZES_NOT_MEASURED, ClosureReason.CAPTURE_MISSING} and not run.fills


@pytest.mark.parametrize("sub", ["journal/school", "research/school", "receipts/data"])
def test_a_home_inside_the_pilots_records_is_refused_before_anything_is_written(sub):
    with pytest.raises(HomeUnderThePilot):
        build_practice_fleet(tf.parts(), sb.SESSION, Scenario.MEDIAN, ROOT / sub / "practice")


def test_a_run_writes_nothing_under_the_pilots_paths(tmp_path):
    """Criterion 15: before and after, the pilot's account, dashcam, counts and receipt folders are the same."""
    watched = [ROOT / "journal", ROOT / "research" / "school", ROOT / "receipts"]
    before = {p: p.stat().st_mtime_ns for w in watched for p in w.rglob("*") if p.is_file()}
    tf.fleet(tmp_path).run(sb.SESSION, RunMode.REPLAY)
    after = {p: p.stat().st_mtime_ns for w in watched for p in w.rglob("*") if p.is_file()}
    assert after == before and any(tmp_path.rglob("*"))


def test_a_window_over_an_unregistered_road_is_refused_by_name():
    """Criterion 16: FINNIFTY and MIDCPNIFTY are not in DATA_SPEND; NIFTY monthly is spent."""
    windows = PracticeWindows()
    for road in (RoadCode.FINNIFTY_MONTHLY, RoadCode.MIDCPNIFTY_MONTHLY):
        assert windows.check(road, sb.SESSION) is PracticeRefusal.NOT_IN_DATA_SPEND
    assert windows.check(RoadCode.NIFTY_MONTHLY, sb.SESSION) is None


def sessions_2023() -> list[date]:
    days = [date(2023, 3, 1) + timedelta(days=i) for i in range(0, 40)]
    return [d for d in days if d.weekday() < 5]


def parts_2023() -> PracticeParts:
    days = sessions_2023()
    chain = sb.DictChain(*[sb.chain(u, d, MONTHLIES_2023, WEEKLIES_2023) for u in ("NIFTY", "BANKNIFTY") for d in days])
    merged: dict = {}
    for code in (RoadCode.NIFTY_MONTHLY, RoadCode.NIFTY_WEEKLY, RoadCode.BANKNIFTY_MONTHLY):
        for day in (date(2023, 3, 31), date(2023, 4, 3)):
            merged.update(sb.full_model(code, 0.01, day, MONTHLIES_2023, WEEKLIES_2023).by_session)
    return PracticeParts(
        tf.CFG, ROOT, tf.FACTOR_FILE, CALENDAR_2023, chain, sb.TERMS, PracticeWindows(), SpreadModel(merged)
    )


def test_a_position_opened_before_the_stt_change_and_met_after_it_keeps_its_own_charges(tmp_path):
    """Criterion 11: 31 Mar 2023 (STT 0.05%) opens trades; 3 Apr 2023 (0.0625%) reads them back and runs."""
    parts, margin = parts_2023(), (lambda cfg: FixedMargin())
    first = build_practice_fleet(parts, date(2023, 3, 31), Scenario.MEDIAN, tmp_path, margin).run(
        date(2023, 3, 31), RunMode.REPLAY
    )
    second = build_practice_fleet(parts, date(2023, 4, 3), Scenario.MEDIAN, tmp_path, margin).run(
        date(2023, 4, 3), RunMode.REPLAY
    )
    assert (
        second.decisions and not second.status
    )  # the account read back under the later mapping did not stop the fleet
    filled = [leg for fill in first.fills for leg in fill.legs]
    assert filled and len(filled) == sum(len(f.legs) for f in first.fills)
    for leg in filled:  # each leg was charged by the 31 Mar mapping (0.05% STT on sells), not 3 Apr's or today's
        expected = order_charges(leg.price, leg.units, leg.side, sb.TERMS.charges(date(2023, 3, 31)))
        assert leg.charges == pytest.approx(expected)
        if leg.side == "sell":
            today = order_charges(leg.price, leg.units, leg.side, sb.CHARGES)
            assert leg.charges < today
