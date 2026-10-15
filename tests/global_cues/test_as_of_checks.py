"""Story A17: an India date uses only a value dated before it (US holidays fall back to the last US close), live use
needs a value first seen before that day's 09:15 IST; gaps and RBI/FBIL differences are listed, never filled."""

from datetime import date

from fno.global_cues.as_of import value_for
from fno.global_cues.checks import gap_rows, overlap_rows


def row(day, value, seen="2026-10-15T06:15:00+05:30"):
    return {"value_date": day, "value": value, "first_seen_at": seen}


ROWS = [
    row("2026-01-16", "100.0", "2026-01-17T06:00:00+05:30"),  # Friday, seen Saturday morning IST
    row("2026-01-20", "101.0", "2026-01-21T10:00:00+05:30"),  # Tuesday (Monday 19 Jan: US holiday), seen late
]


def test_tuesday_after_a_us_monday_holiday_uses_fridays_close():
    assert value_for(ROWS, date(2026, 1, 20), live_only=True)["value"] == "100.0"


def test_a_same_date_value_is_never_used():
    assert value_for(ROWS, date(2026, 1, 16), live_only=False) is None


def test_live_use_needs_the_value_seen_before_that_days_open():
    assert value_for(ROWS, date(2026, 1, 21), live_only=False)["value"] == "101.0"  # research: the rule's answer
    assert value_for(ROWS, date(2026, 1, 21), live_only=True)["value"] == "100.0"  # seen at 10:00, after 09:15


def test_weekday_gaps_and_repeated_values_are_listed():
    rows = [row("2026-10-08", "1.0"), row("2026-10-09", "1.0"), row("2026-10-13", "2.0")]
    assert gap_rows("x", rows) == [
        ("x", "2026-10-09", "repeated_previous_value"),
        ("x", "2026-10-12", "weekday_without_value"),
    ]


def test_rbi_and_fbil_differences_are_listed_over_their_common_span():
    rbi = {"2018-07-09": "68.0", "2018-07-10": "68.79", "2018-07-11": "68.8", "2026-10-14": "95.0"}
    fbil = {"2018-07-10": "68.7942", "2018-07-11": "68.8", "2018-07-12": "68.9", "2026-10-07": "96.6"}
    assert overlap_rows(rbi, fbil) == [
        ("2018-07-10", "differs", "68.79", "68.7942"),
        ("2018-07-12", "only_fbil", "", "68.9"),
        ("2026-10-07", "only_fbil", "", "96.6"),
    ]
