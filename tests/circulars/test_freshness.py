"""A20b criterion 7: NSE is stale when no circular is dated the previous session (judged on a session day, a holiday
and a weekend); SEBI when its newest circular is over 45 days old (45 fine, 46 stale); an empty list is stale."""

from datetime import date, timedelta

from fno.circulars.freshness import NewestAgeFreshness, PreviousSessionFreshness
from fno.circulars.model import NSE, SEBI, Circular
from fno.storage.wiring import build_session_calendar

NSE_FRESH = PreviousSessionFreshness(build_session_calendar())


def circular(source, day):
    return Circular(source, "n", day, "", "", "s", f"https://x/{day}")


def test_nse_judges_the_previous_session_on_a_session_day_a_holiday_and_a_weekend():
    cases = {
        date(2026, 10, 16): date(2026, 10, 15),  # Friday: Thursday
        date(2026, 10, 2): date(2026, 10, 1),  # Gandhi Jayanti holiday: Thursday 1 Oct
        date(2026, 10, 18): date(2026, 10, 16),  # Sunday: Friday
    }
    for today, previous in cases.items():
        assert NSE_FRESH(NSE, [circular(NSE, previous)], today) is None, today
        problem = NSE_FRESH(NSE, [circular(NSE, today), circular(NSE, previous - timedelta(days=1))], today)
        assert problem.key == "nse:stale" and str(previous) in problem.text, today


def test_nse_empty_list_is_stale():
    assert NSE_FRESH(NSE, [], date(2026, 10, 16)).key == "nse:stale"


def test_sebi_45_days_is_fine_46_is_stale_and_empty_is_stale():
    today, sebi = date(2026, 10, 16), NewestAgeFreshness()
    assert sebi(SEBI, [circular(SEBI, today - timedelta(days=45))], today) is None
    assert sebi(SEBI, [circular(SEBI, today - timedelta(days=46))], today).key == "sebi:stale"
    assert sebi(SEBI, [], today).key == "sebi:stale"


def test_beyond_the_calendar_is_its_own_problem_not_a_crash():
    problem = NSE_FRESH(NSE, [], date(2027, 1, 2))  # the calendar holds no 2027 rows yet
    assert problem.key == "nse:calendar" and "does not cover 2027-01-02" in problem.text
