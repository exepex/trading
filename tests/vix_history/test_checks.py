"""Story A15: gaps are listed against NSE's calendar and never filled, doubtful levels are listed and kept, and every
disagreement with the index-close VIX closes is listed (rounding apart from real differences), never corrected."""

from datetime import date

from fno.research_data.calendar import CsvSessionCalendar
from fno.vix_history.checks import gap_rows, level_rows, overlap_rows

SOURCE = "https://nsearchives.nseindia.com/content/circulars/example.pdf"
CALENDAR = CsvSessionCalendar(
    "date,kind,description,source_url\n"
    f"2024-03-01,holiday,example holiday,{SOURCE}\n"
    f"2024-03-02,special,special Saturday session,{SOURCE}\n"
)


def test_a_session_without_a_row_and_a_row_on_a_closed_day_are_listed():
    days = {date(2024, 2, 29), date(2024, 3, 1), date(2024, 3, 4)}
    assert gap_rows(days, CALENDAR) == [
        ("2024-03-01", "row_on_closed_day", "a VIX row on a day the NSE calendar calls closed"),
        ("2024-03-02", "gap", "NSE calendar session with no VIX row"),
    ]


def test_muhurat_and_special_session_rows_are_labelled():
    calendar = CsvSessionCalendar(
        "date,kind,description,source_url\n"
        f"2024-01-20,special,special Saturday session,{SOURCE}\n"
        f"2024-11-01,muhurat,Diwali muhurat session,{SOURCE}\n"
    )
    days = {date(2024, 1, 19), date(2024, 1, 20), date(2024, 1, 22)}
    assert gap_rows(days, calendar) == [
        ("2024-01-20", "special_session", "a VIX row on a weekend special session, not a regular day")
    ]
    muhurat = {date(2024, 10, 31), date(2024, 11, 1), date(2024, 11, 4)}
    assert gap_rows(muhurat, calendar)[0][:2] == ("2024-11-01", "muhurat_session")


def test_before_the_calendar_a_missing_weekday_is_unverified_and_a_weekend_row_is_listed():
    days = {date(2012, 1, 6), date(2012, 1, 7), date(2012, 1, 10)}  # Fri, Sat, Tue
    assert gap_rows(days, CALENDAR) == [
        ("2012-01-07", "weekend_row", "a VIX row on a weekend; the session calendar does not cover this year"),
        ("2012-01-09", "unverified", "weekday without a row; the session calendar does not cover this year"),
    ]


def level(day, o, h, lo, c):
    return {"date": day, "open": o, "high": h, "low": lo, "close": c}


def test_a_zero_level_and_a_close_outside_the_days_range_are_listed_as_published():
    rows = [
        level("2013-08-22", "28.09", "29.86", "27.99", "27.68"),
        level("2021-02-12", "0.0", "0.0", "0.0", "23.045"),
        level("2021-02-15", "23.0", "24.0", "22.0", "23.5"),
    ]
    assert level_rows(rows) == [
        ("2013-08-22", "outside_low_high", "28.09", "29.86", "27.99", "27.68"),
        ("2021-02-12", "not_positive", "0.0", "0.0", "0.0", "23.045"),
    ]


def test_every_disagreement_with_the_index_close_closes_is_listed_and_rounding_is_told_apart():
    history = {
        date(2016, 12, 30): "15.0",  # before the overlap: not compared
        date(2017, 1, 2): "15.83",
        date(2017, 1, 3): "15.9575",
        date(2017, 1, 4): "15.065",
        date(2017, 1, 5): "15.5",
        date(2017, 1, 9): "15.1",
    }
    index_close = {
        date(2017, 1, 2): "15.83",
        date(2017, 1, 3): "15.96",
        date(2017, 1, 4): "15.07",  # half-up: 15.065 -> 15.07
        date(2017, 1, 5): "15.52",
        date(2017, 1, 6): "15.4",
        date(2017, 1, 9): "15.1000",
    }
    assert overlap_rows(history, index_close) == [
        ("2017-01-03", "rounded", "15.9575", "15.96"),
        ("2017-01-04", "rounded", "15.065", "15.07"),
        ("2017-01-05", "differs", "15.5", "15.52"),
        ("2017-01-06", "only_in_index_close", "", "15.4"),
    ]
