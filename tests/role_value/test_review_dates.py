"""S1's scheduled review dates (story F9a criterion 4): the sixth full month after the common start, then every 3
months, each on the month's last NSE session."""

from datetime import date

from fno.evaluation.review_dates import review_dates
from tests.scoreboard.matched_builders import weekdays

HOLIDAY = date(2027, 6, 30)  # a Wednesday: June 2027's last calendar weekday is a holiday here


def sessions(first: date, last: date) -> list[date]:
    return [d for d in weekdays(first, last) if d != HOLIDAY]


def test_the_first_review_is_the_last_session_of_the_sixth_full_month_then_every_three_months():
    found = review_dates(date(2026, 12, 2), sessions, date(2028, 1, 1))
    assert found == [date(2027, 6, 29), date(2027, 9, 30), date(2027, 12, 31)]


def test_a_month_ending_on_a_holiday_reviews_on_its_last_session_before_it():
    assert review_dates(date(2026, 12, 2), sessions, date(2027, 6, 30))[0] == date(2027, 6, 29)


def test_no_review_before_its_date():
    assert review_dates(date(2026, 12, 2), sessions, date(2027, 6, 28)) == []
