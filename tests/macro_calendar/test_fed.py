"""A20c criterion 11: the Fed's FOMC page (16 Oct 2026) gives 8 decision days for each year from the run's year on;
the decision day is a range's last day, across months too ("Apr/May 30-1"); a notation vote is not a decision; 7
meetings, no panel for the run's year and an empty page are refused."""

from datetime import date
from pathlib import Path

import pytest

from fno.macro_calendar.fed import read_fomc
from fno.macro_calendar.model import CalendarFailed

PAGE = (Path(__file__).parents[1] / "fixtures" / "macro_calendar" / "fomccalendars_16102026.html").read_text()


def test_eight_decision_days_a_year_from_the_run_s_year_on():
    days = [d.day for d in read_fomc(PAGE, date(2026, 10, 16))]
    assert len(days) == 16 and days[0] == date(2026, 1, 28) and days[7] == date(2026, 12, 9)
    assert days[-1] == date(2027, 12, 8) and all(d.year >= 2026 for d in days)


def test_a_range_across_months_ends_in_the_later_month_and_a_notation_vote_is_not_a_decision():
    assert date(2024, 5, 1) in [d.day for d in read_fomc(PAGE, date(2024, 6, 1))]  # "Apr/May 30-1"
    days_2025 = [d.day for d in read_fomc(PAGE, date(2025, 1, 2)) if d.day.year == 2025]
    assert len(days_2025) == 8 and date(2025, 8, 22) not in days_2025  # "22 (notation vote)"


def test_seven_meetings_no_panel_for_the_year_or_an_empty_page_are_refused():
    with pytest.raises(CalendarFailed, match="2026 has 7 scheduled meetings"):
        read_fomc(PAGE.replace(">27-28</div>", ">TBD</div>", 1), date(2026, 10, 16))
    with pytest.raises(CalendarFailed, match="no panel for 2029"):
        read_fomc(PAGE, date(2029, 1, 2))
    with pytest.raises(CalendarFailed):
        read_fomc("", date(2026, 10, 16))


def test_the_adapter_s_period_runs_from_the_run_s_year_to_its_last_listed_year():
    from fno.macro_calendar.fed import URL, FedFomcCalendar

    class Answer:
        status_code, content = 200, PAGE.encode()

    class Session:
        def get(self, url, timeout):
            assert url == URL
            return Answer()

    calendar = FedFomcCalendar(Session()).fetch(date(2026, 10, 16))
    assert calendar.period == (date(2026, 1, 1), date(2027, 12, 31)) and len(calendar.dates) == 16
