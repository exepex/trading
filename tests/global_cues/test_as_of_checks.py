"""Story A17: an India date uses only a value dated before it (US holidays fall back to the last US close), live use
needs a value first seen before that day's 09:15 IST; gaps and RBI/FBIL differences are listed, never filled."""

from datetime import date, datetime, time

from fno.global_cues.as_of import DECISION, OPEN, value_for
from fno.global_cues.checks import gap_rows, overlap_rows
from fno.global_cues.other_sources import RbiUsdInrSource
from fno.global_cues.us_index_sources import CboeSp500Source
from fno.models import IST


def row(day, value, seen="2026-10-15T06:15:00+05:30"):
    return {"value_date": day, "value": value, "first_seen_at": seen}


US = CboeSp500Source().available_at  # 16:00 New York on the value date
RATE = RbiUsdInrSource().available_at  # 13:30 IST on the value date
ROWS = [
    row("2026-01-16", "100.0", "2026-01-17T06:00:00+05:30"),  # Friday, seen Saturday morning IST
    row("2026-01-20", "101.0", "2026-01-21T10:00:00+05:30"),  # Tuesday (Monday 19 Jan: US holiday), seen late
]


def test_a_us_close_is_final_at_16_00_new_york_whatever_the_season():
    assert US(date(2026, 7, 10)) == datetime(2026, 7, 11, 1, 30, tzinfo=IST)  # US summer time
    assert US(date(2026, 1, 16)) == datetime(2026, 1, 17, 2, 30, tzinfo=IST)  # winter
    assert RATE(date(2026, 10, 14)) == datetime(2026, 10, 14, 13, 30, tzinfo=IST)


def test_tuesday_after_a_us_monday_holiday_uses_fridays_close():
    assert value_for(ROWS, date(2026, 1, 20), OPEN, True, US)["value"] == "100.0"


def test_a_same_date_us_close_is_never_used_even_at_15_00():
    assert value_for(ROWS, date(2026, 1, 16), DECISION, False, US) is None


def test_live_use_needs_the_value_seen_before_the_cutoff():
    assert value_for(ROWS, date(2026, 1, 21), OPEN, False, US)["value"] == "101.0"  # research: the rule's answer
    assert value_for(ROWS, date(2026, 1, 21), OPEN, True, US)["value"] == "100.0"  # seen at 10:00, after 09:15
    assert value_for(ROWS, date(2026, 1, 21), DECISION, True, US)["value"] == "101.0"  # 10:00 is before 15:00


def test_the_same_days_reference_rate_counts_at_15_00_not_at_09_15():
    rates = [
        row("2026-10-13", "95.2477", "2026-10-13T14:00:00+05:30"),
        row("2026-10-14", "95.0317", "2026-10-14T13:45:00+05:30"),
    ]
    assert value_for(rates, date(2026, 10, 14), OPEN, True, RATE)["value_date"] == "2026-10-13"
    assert value_for(rates, date(2026, 10, 14), DECISION, True, RATE)["value_date"] == "2026-10-14"


def test_at_exactly_the_publication_time_a_value_is_not_yet_usable():
    rates = [row("2026-10-14", "95.0317", "2026-10-14T13:00:00+05:30")]
    assert value_for(rates, date(2026, 10, 14), time(13, 30), False, RATE) is None
    assert value_for(rates, date(2026, 10, 14), time(13, 31), False, RATE)["value"] == "95.0317"


def test_weekday_gaps_and_repeated_values_are_listed():
    rows = [row("2026-10-08", "1.0"), row("2026-10-09", "1.0"), row("2026-10-13", "2.0")]
    assert gap_rows("x", rows) == [
        ("x", "2026-10-09", "repeated_previous_value"),
        ("x", "2026-10-12", "weekday_without_value"),
    ]


def test_rbi_and_fbil_differences_are_listed_on_the_dates_both_publish_without_a_rate():
    rbi = {"2018-07-09": "70.0", "2018-07-10": "70.12", "2018-07-11": "70.5", "2026-10-14": "90.0"}  # made up
    fbil = {"2018-07-10": "70.1234", "2018-07-11": "70.5", "2018-07-12": "70.9", "2026-10-07": "91.0"}
    assert overlap_rows(rbi, fbil) == [("2018-07-10", "differs")]  # A17d: a public row never holds FBIL's rate
