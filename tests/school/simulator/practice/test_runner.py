"""The practice runner and its report (MS-SIM-d3)."""

from dataclasses import replace
from datetime import date, timedelta

import pytest

from fno.school.constants import OptionKind, RoadCode
from fno.school.execution import practice_wiring
from fno.school.fakes import FakeSettlementSource
from fno.school.simulator.constants import PRACTICE_LABEL, PracticeRefusal
from fno.school.simulator.practice.render import LABELS, render
from fno.school.simulator.practice.runner import PracticeRunner
from fno.school.simulator.practice.window import RunWindow, WindowRefused
from fno.school.simulator.spreads.model import Scenario
from tests.school.safety.law_builders import FixedMargin
from tests.school.simulator.practice import test_fleet as tf
from tests.school.simulator.source import builders as sb

NIFTY = (RoadCode.NIFTY_MONTHLY, RoadCode.NIFTY_WEEKLY, RoadCode.BANKNIFTY_MONTHLY)
WINDOW = RunWindow(sb.SESSION - timedelta(days=4), sb.SESSION, NIFTY)  # Thu 3 Mar to Mon 7 Mar: three sessions


@pytest.fixture(autouse=True)
def archive_stubbed(monkeypatch):
    monkeypatch.setattr(practice_wiring, "build_settlement_source", lambda: FakeSettlementSource({}))


def runner(tmp_path, parts=None):
    return PracticeRunner(parts or tf.parts(), tmp_path, margin_for=lambda cfg: FixedMargin())


def test_a_window_runs_every_scenario_over_every_session(tmp_path):
    report = runner(tmp_path).run(WINDOW)
    assert list(report.scenarios) == [Scenario.MEDIAN, Scenario.P75, Scenario.P95]
    sessions = WINDOW.sessions(sb.CALENDAR)
    assert sessions and all(r.sessions_run == len(sessions) for r in report.scenarios.values())
    for result in report.scenarios.values():
        assert result.drivers and len(sessions) == 3
        assert all(
            d.scheduled and d.scheduled % len(sessions) == 0 for d in result.drivers.values()
        )  # a driver's roads x sessions


def test_coverage_is_read_once_per_road_day_not_once_per_scenario(tmp_path):
    report = runner(tmp_path).run(WINDOW)
    days = {(c.session, c.road) for c in report.coverage}
    assert len(report.coverage) == len(days) > 0
    assert all(c.legs == c.priced + c.untraded + c.impossible + c.unsellable + c.insufficient for c in report.coverage)


def test_each_scenario_has_its_own_home_and_accounts(tmp_path):
    runner(tmp_path).run(WINDOW)
    assert {p.name for p in tmp_path.iterdir()} == {"median", "p75", "p95"}


def test_counts_come_from_the_fleets_own_counts_files_and_executed_never_exceeds_fillable(tmp_path):
    report = runner(tmp_path).run(WINDOW)
    for result in report.scenarios.values():
        for found in result.drivers.values():
            assert found.eligible >= found.fillable >= found.executed >= 0
    assert sum(d.fillable for d in report.scenarios[Scenario.MEDIAN].drivers.values()) > 0


def test_account_trades_are_executed_not_size_shared_under_the_practice_rules(tmp_path):
    """The silent zero: fills happened but every account entry read `unavailable: size_shared` (fixed by MS-P1j)."""
    report = runner(tmp_path).run(WINDOW)
    assert sum(d.executed for d in report.scenarios[Scenario.MEDIAN].drivers.values()) > 0


def test_the_report_counts_impossible_legs_apart_from_refusals(tmp_path):
    """Criterion 14: the impossible share is its own line, not folded into the refusals."""
    base = sb.chain("NIFTY", sb.SESSION)
    target = (sb.SPOT + 100, OptionKind.CALL, sb.MONTHLIES[0])
    rows = tuple(replace(r, close=392.0) if (r.strike, r.kind, r.expiry) == target else r for r in base.rows)
    parts = tf.parts()
    parts.chain.days[("NIFTY", sb.SESSION)] = replace(base, rows=rows)
    report = runner(tmp_path, parts).run(WINDOW)
    text = "\n".join(render(report))
    assert any(c.impossible > 0 for c in report.coverage)
    assert "impossible" in text and "refused by margin" in text


def test_every_line_carries_the_label_and_the_required_labels_come_first(tmp_path):
    lines = render(runner(tmp_path).run(WINDOW))
    assert lines and all(line.startswith(PRACTICE_LABEL + " | ") for line in lines)
    text = "\n".join(lines)
    for label in LABELS:
        assert label in text
    assert "scenario median" in text and "scenario p75" in text and "scenario p95" in text


def test_a_window_over_an_unregistered_road_is_refused_by_name_before_any_session_is_read(tmp_path):
    parts = tf.parts()
    window = RunWindow(WINDOW.first, WINDOW.last, (RoadCode.NIFTY_MONTHLY, RoadCode.FINNIFTY_MONTHLY))
    with pytest.raises(WindowRefused, match="not_in_data_spend") as raised:
        runner(tmp_path, parts).run(window)
    assert raised.value.road is RoadCode.FINNIFTY_MONTHLY and raised.value.reason is PracticeRefusal.NOT_IN_DATA_SPEND
    assert parts.chain.asked == [] and not list(tmp_path.iterdir())  # nothing read, nothing written


def test_a_window_after_the_data_end_is_refused_by_name(tmp_path):
    late = RunWindow(date(2026, 10, 12), date(2026, 10, 14), (RoadCode.NIFTY_MONTHLY,))
    with pytest.raises(WindowRefused, match="2026-10-14"):
        runner(tmp_path).run(late)


def test_a_window_needs_roads_and_ordered_days():
    with pytest.raises(ValueError):
        RunWindow(sb.SESSION, sb.SESSION - timedelta(days=1), NIFTY)
    with pytest.raises(ValueError):
        RunWindow(sb.SESSION, sb.SESSION, ())


# ---- the report's arithmetic -----------------------------------------------------------------------------------------


def outcome(driver: str, net: float, is_ticket: bool = False, position: str = "p"):
    from datetime import datetime

    from fno.models import IST
    from fno.school.constants import ExitReason
    from fno.school.contracts.accounts import FilledLeg, FillResult
    from fno.school.contracts.records import OutcomeRecord

    leg = FilledLeg(sb_key(), "sell", 50, 99.0, 12.0)
    filled = FillResult((leg,), filled_at=datetime(2022, 3, 7, 15, 30, tzinfo=IST), rests_on="x")
    return OutcomeRecord(position, driver, RoadCode.NIFTY_MONTHLY, "sha", filled, filled, ExitReason.EXPIRY, net, 0.0,
                         net, 0.1, 0.0, is_ticket)  # fmt: skip


def sb_key():
    from tests.school.contracts import builders as b

    return b.key(1000.0)


class SealedOutcomes:
    """A fleet's dashcam holding one sealed outcomes file."""

    def __init__(self, records):
        self.records = tuple(records)
        self.dashcam = self

    def find(self, session, slot, kind):
        return object() if self.records else None

    def read(self, seal):
        return self.records


def test_a_drivers_net_is_the_account_trades_only_and_tickets_are_never_added(tmp_path):
    from fno.school.simulator.practice.report import ScenarioResult

    result = ScenarioResult()
    fleet = SealedOutcomes([outcome("A@1", 100.0, position="1"), outcome("A@1", -30.0, position="2"),
                            outcome("A@1", 500.0, is_ticket=True, position="3")])  # fmt: skip
    PracticeRunner._outcomes(result, fleet, sb.SESSION)
    found = result.drivers["A@1"]
    assert found.net == pytest.approx(70.0) and found.closed_trades == 2  # the Rs 500 ticket is not in rupees


def test_the_impossible_share_is_legs_over_legs_and_zero_without_legs():
    from fno.school.simulator.practice.report import RoadDayCoverage

    day = RoadDayCoverage(sb.SESSION, RoadCode.NIFTY_MONTHLY, 40, 20, 8, 10, 2, 0)
    assert day.impossible_share == 0.25
    assert RoadDayCoverage(sb.SESSION, RoadCode.NIFTY_MONTHLY, 0, 0, 0, 0, 0, 0).impossible_share == 0.0


def test_the_impossible_line_gives_the_share_of_legs(tmp_path):
    report = runner(tmp_path).run(WINDOW)
    legs = sum(c.legs for c in report.coverage)
    impossible = sum(c.impossible for c in report.coverage)
    assert f"impossible {impossible} ({impossible / legs:.0%})" in "\n".join(render(report))


def test_the_archive_is_read_before_the_fleet_runs_so_the_drivers_deadline_measures_the_rule(tmp_path, monkeypatch):
    """The first real-data run: a cold Drive read inside the fleet made CS1 `unavailable: deadline`."""
    from fno.school.fleet.runner import SchoolFleet
    from fno.school.simulator.practice.cached_chain import CachedChain

    parts = tf.parts()
    underlying = parts.chain
    reads = {"inside": False, "cold": 0}

    class Spy:
        def day(self, name, session):
            if reads["inside"]:
                reads["cold"] += 1  # a read that reached the archive while the fleet was running
            return underlying.day(name, session)

    original = SchoolFleet.run

    def watched(self, session, mode):
        reads["inside"] = True
        try:
            return original(self, session, mode)
        finally:
            reads["inside"] = False

    monkeypatch.setattr(SchoolFleet, "run", watched)
    from dataclasses import replace as swap

    cached = swap(parts, chain=CachedChain(Spy()))
    runner(tmp_path, cached).run(WINDOW)
    assert reads["cold"] == 0
