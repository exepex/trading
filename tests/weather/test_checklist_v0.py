"""Story M1, criteria 1 and 2: weather baseline v0 reproduces response 94 (as of close) and reads point in time."""

import csv
import json
import math
from dataclasses import replace
from datetime import date

import pytest

from fno.config import ROOT
from fno.constants import WeatherColour
from fno.weather.checklist_v0 import AMBER_LIMITS, RED_LIMITS, Event, Row, V0Inputs, colour_as_of_close, v0_colour
from fno.weather.v0_live import ChecklistV0
from fno.weather.wiring import EVENTS_FILE, build_weather_days, read_events

from .fakes import days_after, rows_from

STUDY = ROOT / "research" / "2026-10-14-weekly-weather"
CLOSES = ROOT / "research" / "data" / "nifty-panel" / "warmup_closes.csv"
CALM = V0Inputs(1.0, 0.0, 0.005, 0.10)
GREEN, AMBER, RED = WeatherColour.GREEN, WeatherColour.AMBER, WeatherColour.RED


def test_as_of_close_reproduces_all_396_colours_of_response_94():
    rows = [Row(date.fromisoformat(r["date"]), float(r["underlying"]), float(r["vix"]))
            for r in csv.DictReader(CLOSES.open())]  # fmt: skip
    index = {r.day: i for i, r in enumerate(rows)}
    events = read_events(EVENTS_FILE.read_text())
    trades = json.loads((STUDY / "trades.json").read_text())
    found = [
        colour_as_of_close(rows, index[date.fromisoformat(t["entry"])] - 1, events, date.fromisoformat(t["entry"]),
                           date.fromisoformat(t["expiry"]))
        for t in trades
    ]  # fmt: skip
    assert len(trades) == 396
    assert [str(c) for c in found] == [t["weather"] for t in trades]  # every day, not only the counts
    assert {c: found.count(c) for c in (GREEN, AMBER, RED)} == {GREEN: 157, AMBER: 137, RED: 102}


FIELDS = ("vix_ratio", "vix_change5", "move5", "rv10")


@pytest.mark.parametrize("field, red, amber", list(zip(FIELDS, RED_LIMITS, AMBER_LIMITS, strict=True)))
def test_each_threshold_at_just_under_and_just_over(field, red, amber):
    def colour(value):
        return v0_colour(replace(CALM, **{field: value}), event=False)

    assert [colour(red - 1e-9), colour(red), colour(red + 1e-9)] == [AMBER, RED, RED]
    assert [colour(amber - 1e-9), colour(amber), colour(amber + 1e-9)] == [GREEN, AMBER, AMBER]


def test_a_scheduled_event_makes_a_calm_day_amber_but_never_lowers_red():
    assert (v0_colour(CALM, False), v0_colour(CALM, True)) == (GREEN, AMBER)
    assert v0_colour(replace(CALM, rv10=0.30), True) == RED


def _checklist(rows, events=()):
    return ChecklistV0(rows, list(events), days_after(rows, 5))


def test_live_inputs_read_closes_up_to_the_previous_session_only():
    rows = rows_from([0.001] * 300)
    d = rows[280].day
    moved = [*rows[:280], replace(rows[280], close=rows[280].close * 1.05, vix=40.0), *rows[281:]]
    assert _checklist(rows).inputs(d) == _checklist(moved).inputs(d)  # d's own close and VIX are not seen
    assert _checklist(rows).inputs(rows[281].day) != _checklist(moved).inputs(rows[281].day)


def test_live_inputs_need_250_earlier_sessions():
    rows = rows_from([0.001] * 300)
    assert _checklist(rows).inputs(rows[250].day) is None  # 250 rows before d: the last is i = 249
    assert _checklist(rows).inputs(rows[251].day) is not None
    assert _checklist(rows).colour(rows[250].day) is None


def test_live_inputs_are_missing_without_a_vix_close():
    rows = rows_from([0.001] * 300)
    gap = [*rows[:279], replace(rows[279], vix=None), *rows[280:]]
    assert _checklist(gap).inputs(rows[280].day) is None


def test_the_live_event_window_is_d_plus_1_to_d_plus_5_announced_by_d():
    rows = rows_from([0.001] * 300)
    d, days = rows[280].day, [r.day for r in rows]

    def seen(day, announced):
        return _checklist(rows, [Event(day, "rbi_policy", announced)]).events_ahead(d) != []

    assert not seen(d, d)  # the decision day itself is not ahead
    assert seen(days[281], d) and seen(days[285], days[200])  # d+1 and d+5, announced by d
    assert not seen(days[286], d)  # d+6
    assert not seen(days[283], days[281])  # announced after d: not seen on d
    assert _checklist(rows, [Event(days[283], "budget", d)]).colour(d) == AMBER


def test_no_event_rows_and_a_calendar_that_ends_inside_the_window():
    rows = rows_from([0.001] * 300)
    assert _checklist(rows).events_ahead(rows[280].day) == []
    assert _checklist(rows).colour(rows[280].day) == GREEN
    assert _checklist(rows).events_ahead(rows[296].day) is None  # 3 sessions left: no event check, no colour
    assert _checklist(rows).colour(rows[296].day) is None


def test_the_four_inputs_equal_a_hand_computation():
    vix = [10.0] * 130 + [12.0] * 125 + [13.2]  # the previous 250: 125 at 10 and 125 at 12, median 11
    rows = rows_from([0.0] * 250 + [0.01, -0.02, 0.0, 0.0, 0.0], vix)
    found = _checklist(rows).inputs(rows[-1].day + (rows[1].day - rows[0].day))
    assert found.vix_ratio == pytest.approx(1.2) and found.vix_change5 == pytest.approx(13.2 / 12.0 - 1)
    assert found.move5 == pytest.approx(1 - math.exp(-0.02))  # simple return of the -2% log day
    assert found.rv10 == pytest.approx(math.sqrt(252 * (0.01**2 + 0.02**2) / 10))


def test_a_sunday_budget_inside_the_5_sessions_counts_as_an_event():
    """Real case: 29 Jan 2026's 5 regular sessions end on 5 Feb; the Budget is on Sunday 1 Feb (a special session).
    The window is by date, so the Budget counts; its move is inside the 2 Feb return."""
    weather = build_weather_days()
    assert [e.kind for e in weather.v0.events_ahead(date(2026, 1, 29))] == ["budget"]
    assert weather.v0.colour(date(2026, 1, 29)) == AMBER
