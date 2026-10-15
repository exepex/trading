"""LR1's weather and data-health sections: M1 records as written, G7's V6a rule, T1's own card misses."""

from datetime import date, datetime

from fno.learning.health_section import DataHealthSection
from fno.learning.readers import CaptureState
from fno.learning.weather_section import WeatherSection
from fno.learning.week import build_week
from fno.models import IST
from fno.weather.records import WeatherRecords

from .fakes import SATURDAY, WEEK_DAYS, Calendar, Captures, Count, Deliveries

WEEK = build_week(Calendar(), SATURDAY)


def _record(day, colour, label="live", red_share=0.12):
    return {"day": day.isoformat(), "colour": colour, "v0_colour": "AMBER", "label": label, "status": "scored",
            "red_share": red_share, "over_alarming": False, "made_at": ""}  # fmt: skip


def _weather(tmp_path, colours):
    records = WeatherRecords(tmp_path)
    for day, colour in colours.items():
        records.write(day, _record(day, colour))
    return records


def test_a_green_day_followed_by_a_2pct_move_is_a_weather_miss(tmp_path):
    records = _weather(tmp_path, {WEEK_DAYS[0]: "GREEN", WEEK_DAYS[1]: "AMBER", WEEK_DAYS[2]: "GREEN"})
    moves = {WEEK_DAYS[0]: True, WEEK_DAYS[1]: True, WEEK_DAYS[2]: False}  # 14 Oct onwards: not yet resolved
    section = WeatherSection(records, lambda: moves)
    lines = section.lines(WEEK)
    assert "- 2026-10-12: GREEN (v0 AMBER; live, scored); next session 2% move: yes" in lines
    assert "- 2026-10-15: missing (v0 missing; missing, missing); next session 2% move: unresolved" in lines
    assert "Weather misses (GREEN, then a 2% move): 2026-10-12" in lines  # AMBER then a move: counted, not listed
    tally = "GREEN 2 days, 1 with a 2% move; AMBER 1 days, 1 with a 2% move; missing 2 days, 0 with a 2% move"
    assert f"Colours this week: {tally}" in lines
    assert "RED share of the last 250 live records: 12.0%; over-alarming: False" in lines
    assert section.data(WEEK)["misses"] == ["2026-10-12"]


def test_backfill_records_have_no_red_share_line(tmp_path):
    records = WeatherRecords(tmp_path)
    records.write(WEEK_DAYS[0], _record(WEEK_DAYS[0], "GREEN", label="backfill_exploratory"))
    assert "RED share: no live weather record this week" in WeatherSection(records, dict).lines(WEEK)


def _health(captures=None, attempts=None, weather=frozenset(), a16=0):
    return DataHealthSection(Captures(captures or {}), Deliveries(attempts or {}), lambda d: d in weather, Count(a16))


def _delivery(test=False):
    return ("p", {"test": test, "slack": {"sent": True, "outcome": "sent"}, "drive": {"saved": True, "outcome": "ok"},
                  "clock": []})  # fmt: skip


def test_data_health_per_session_and_completeness():
    day = WEEK_DAYS[3]
    section = _health({day: CaptureState(True, datetime(2026, 10, 15, 15, 5, 41, tzinfo=IST)),
                       WEEK_DAYS[0]: CaptureState(False, None)},
                      {day: [_delivery()], WEEK_DAYS[1]: [_delivery(test=True)]}, {day}, a16=3)  # fmt: skip
    lines = section.lines(WEEK)
    assert (
        "- 2026-10-15: 3 pm quotes complete=True, finished 10.7 minutes after 14:55; card ok; weather record yes"
        in lines
    )
    assert "- 2026-10-12: 3 pm quotes complete=False, no finish time; card no card on record for 2026-10-12; weather " \
           "record missing" in lines  # fmt: skip
    assert any(line.startswith("- 2026-10-13:") and "no card on record" in line for line in lines)  # a TEST is no card
    assert "Complete days (capture, card and weather record): 1 of 5" in lines
    assert lines[-1] == "15-minute recorder (A16) live sessions: not enough data yet (3 of 20)"


def test_a16_with_enough_sessions_and_a_holiday_week():
    holiday = build_week(Calendar(closed=WEEK_DAYS), SATURDAY)
    assert holiday.sessions == ()
    assert _health(a16=25).lines(holiday) == ["*Data health*", "no NSE regular session this week",
                                              "15-minute recorder (A16) live sessions: 25 sessions"]  # fmt: skip


def test_week_must_be_named_by_a_saturday():
    import pytest

    from fno.learning.week import NotSaturday, latest_saturday

    with pytest.raises(NotSaturday):
        build_week(Calendar(), date(2026, 10, 16))
    assert latest_saturday(date(2026, 10, 17)) == SATURDAY == latest_saturday(date(2026, 10, 22))
