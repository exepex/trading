"""The NSE session calendar: weekdays are sessions unless listed as holidays; weekend and muhurat sessions listed."""

from datetime import date

import pytest

from fno.research_data.calendar import CALENDAR_FILE, CalendarError, CsvSessionCalendar, load_session_calendar

SOURCE = "https://nsearchives.nseindia.com/content/circulars/example.pdf"
HEADER = "date,kind,description,source_url\n"


def calendar(*rows: str) -> CsvSessionCalendar:
    return CsvSessionCalendar(HEADER + "".join(f"{row},{SOURCE}\n" for row in rows))


SAMPLE = calendar(
    "2024-01-22,holiday,Special holiday",
    "2024-01-20,special,Live session on a Saturday",
    "2024-11-01,muhurat,Diwali muhurat trading",
)


def test_weekday_holiday_is_not_a_session():
    assert SAMPLE.is_session(date(2024, 1, 22)) is False
    assert SAMPLE.session_kind(date(2024, 1, 22)) is None


def test_special_saturday_and_muhurat_sessions():
    assert SAMPLE.session_kind(date(2024, 1, 20)) == "special"
    assert SAMPLE.session_kind(date(2024, 11, 1)) == "muhurat"  # a session even on a weekday holiday
    assert SAMPLE.session_kind(date(2024, 1, 23)) == "regular"
    assert SAMPLE.is_session(date(2024, 1, 21)) is False  # an ordinary Sunday


def test_neighbouring_sessions_skip_closed_days():
    assert SAMPLE.next_session(date(2024, 1, 19)) == date(2024, 1, 20)
    assert SAMPLE.next_session(date(2024, 1, 20)) == date(2024, 1, 23)  # Sunday, then the Monday holiday
    assert SAMPLE.previous_session(date(2024, 1, 23)) == date(2024, 1, 20)
    assert SAMPLE.sessions(date(2024, 1, 19), date(2024, 1, 23)) == [
        date(2024, 1, 19),
        date(2024, 1, 20),
        date(2024, 1, 23),
    ]


def test_day_outside_the_covered_years_raises_instead_of_guessing():
    with pytest.raises(CalendarError, match="outside the calendar"):
        SAMPLE.is_session(date(2025, 1, 2))
    with pytest.raises(CalendarError, match="outside the calendar"):
        SAMPLE.previous_session(date(2024, 1, 1))  # never walks past the covered range


@pytest.mark.parametrize(
    "text, message",
    [
        (HEADER + "2024-01-22,holiday,x,\n", "source link"),
        (HEADER + "2024-01-22,closed,x," + SOURCE + "\n", "kind must be"),
        (HEADER + "2024-01-20,holiday,x," + SOURCE + "\n", "weekend day"),
        (HEADER + "2024-01-22,special,x," + SOURCE + "\n", "weekday"),
        (HEADER + "2024-01-22,holiday,x," + SOURCE + "\n2024-01-22,holiday,y," + SOURCE + "\n", "twice"),
        (HEADER + "2022-01-26,holiday,x," + SOURCE + "\n2024-01-22,holiday,y," + SOURCE + "\n", "2023"),
        ("day,kind\n2024-01-22,holiday\n", "columns"),
    ],
)
def test_invalid_calendar_files_are_refused(text, message):
    with pytest.raises(CalendarError, match=message):
        CsvSessionCalendar(text)


def test_fingerprint_changes_with_the_file():
    assert SAMPLE.calendar_sha256() != calendar("2024-01-26,holiday,Republic Day").calendar_sha256()


def test_committed_calendar_is_valid_and_sourced():
    committed = load_session_calendar(CALENDAR_FILE)
    assert committed.first <= date(2019, 1, 1) and committed.last >= date(2026, 12, 31)
