"""LM1 criterion 3: each check fires at its threshold and stays quiet just below it; criteria 2 and 4: nothing runs
with no position, a mark the monitor cannot use gives only the stale WARNING, an unmarked leg gives "cannot mark"."""

from __future__ import annotations

import pytest

from fno.monitor.checks import (
    WAITING_CHECKS,
    BigMove,
    ExitRuleReached,
    ExpiryNear,
    LossUsed,
    QuotesStale,
    ShortStrikeNear,
)
from fno.monitor.model import DANGER, DESK, ONCE, WARNING
from fno.monitor.monitor import PositionMonitor
from fno.research_data.calendar import load_session_calendar
from fno.storage.wiring import CALENDAR_FILE

from .fixtures import DAY, at, mark, settings, spread

CALENDAR = load_session_calendar(CALENDAR_FILE)


def monitor(**changes) -> PositionMonitor:
    s = settings(**changes)
    checks = [LossUsed(s), ShortStrikeNear(s), ExitRuleReached(s), BigMove(s), ExpiryNear(s, CALENDAR)]
    return PositionMonitor(s, checks, QuotesStale(s))


@pytest.mark.parametrize(
    ("loss", "severity"), [(4999.0, None), (5000.0, WARNING), (7999.0, WARNING), (8000.0, DANGER), (-300.0, None)]
)
def test_loss_used_fires_at_50_and_80_percent(loss, severity):
    found = LossUsed(settings()).find(mark(), [spread(loss=loss)])
    assert [c.severity for c in found] == ([severity] if severity else [])


def test_an_unmarked_position_says_cannot_mark_and_gives_no_value():
    (found,) = LossUsed(settings()).find(mark(), [spread(loss=None)])
    assert (found.check, found.severity) == ("cannot_mark", WARNING)
    assert "Rs" not in found.facts and "cannot be measured" in found.facts


def test_a_position_that_cannot_lose_is_quiet():
    assert LossUsed(settings()).find(mark(), [spread(loss=0.0, max_loss=0.0)]) == []


@pytest.mark.parametrize(("level", "fires"), [(24620.0, True), (24625.0, False), (24376.0, False), (24380.0, True)])
def test_short_strike_near_fires_within_half_a_percent(level, fires):
    found = ShortStrikeNear(settings()).find(mark(level=level), [spread(short=24500.0)])
    assert bool(found) is fires
    assert all(c.severity == DANGER for c in found)


def test_bought_strikes_never_count_as_short():
    assert ShortStrikeNear(settings()).find(mark(level=24300.0), [spread(short=24500.0)]) == []


@pytest.mark.parametrize(("level", "key"), [(25374.9, None), (25375.0, "big_move:above:1.50"),
                                            (25499.9, "big_move:above:1.50"), (25500.0, "big_move:above:2.00"),
                                            (24625.0, "big_move:below:1.50")])  # fmt: skip
def test_big_move_fires_at_1_5_percent_once_per_further_step(level, key):
    found = BigMove(settings()).find(mark(level=level), [spread(), spread("T2")])
    assert [c.key for c in found] == ([key] if key else [])
    assert all(c.scope == DESK and c.repeat == ONCE for c in found)


def test_big_move_without_a_step_is_one_hourly_desk_condition():
    (found,) = BigMove(settings(big_move_step_pct=None)).find(mark(level=24000.0), [spread(), spread("T2")])
    assert (found.key, found.repeat, found.scope) == ("big_move:below", "hourly", DESK)
    assert "2 open positions" in found.facts


def test_big_move_needs_the_previous_level():
    assert BigMove(settings()).find(mark(level=20000.0, previous=None), [spread()]) == []


def test_each_exit_rule_reached_is_information_once_and_a_handled_rule_is_quiet():
    rules = ("profit_target", "stop_loss", "time_exit")
    found = ExitRuleReached(settings()).find(mark(), [spread(exit_rules_reached=rules)])
    assert [c.key.split(":")[-1] for c in found] == list(rules)
    assert all(c.information_only and c.repeat == ONCE for c in found)
    handled = spread(exit_rules_reached=("stop_loss",), exit_rules_handled=("stop_loss",))
    assert ExitRuleReached(settings()).find(mark("15:30"), [handled]) == []


def test_expiry_near_warns_from_the_set_number_of_sessions_before():
    one, two = CALENDAR.next_session(DAY), CALENDAR.next_session(CALENDAR.next_session(DAY))
    check = ExpiryNear(settings(), CALENDAR)
    assert [c.severity for c in check.find(mark(), [spread(expiry=one)])] == [WARNING]
    assert check.find(mark(), [spread(expiry=two)]) == []
    assert len(check.find(mark(), [spread(expiry=DAY)])) == 1


def test_quotes_stale_from_30_minutes_without_a_usable_mark():
    stale = QuotesStale(settings())
    start = at("09:15")
    assert stale.find(mark("10:29", status="missed", last_good=at("10:00")), start) == []
    (found,) = stale.find(mark("10:30", status="missed", last_good=at("10:00")), start)
    assert (found.severity, found.scope) == (WARNING, DESK)
    assert stale.find(mark("09:45", status="missed", last_good=None), start)  # nothing usable since the open


def test_no_position_runs_no_check():
    findings = monitor().find(mark(level=20000.0, status="missed", last_good=at("09:15")), [])
    assert (findings.positions, findings.conditions) == (0, ())


def test_an_unusable_mark_gives_only_the_stale_warning():
    bad = mark("11:00", level=20000.0, status="failed", last_good=at("10:15"))
    findings = monitor().find(bad, [spread(loss=9000.0, short=20000.0)])
    assert [c.check for c in findings.conditions] == ["quotes_stale"]


def test_an_incomplete_mark_is_checked_only_when_the_setting_allows():
    incomplete = mark(level=24500.0, status="incomplete")
    assert monitor().find(incomplete, [spread()]).conditions
    assert monitor(check_incomplete_marks=False).find(incomplete, [spread()]).conditions == ()


def test_vix_and_weather_checks_wait_and_are_never_built():
    assert set(WAITING_CHECKS) == {"vix_jump", "weather_upgrade"}
    built = {c.name for c in monitor().checks}
    assert not built & set(WAITING_CHECKS)


@pytest.mark.parametrize(("short", "fires"), [(24875.0, True), (24874.0, False), (25125.0, True)])
def test_short_strike_exactly_half_a_percent_away_fires(short, fires):
    found = ShortStrikeNear(settings()).find(mark(level=25000.0), [spread(short=short)])
    assert bool(found) is fires
