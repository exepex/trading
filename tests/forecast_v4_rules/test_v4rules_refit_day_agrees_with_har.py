"""Judge 585's ruling on the deferred HAR fold: until one function serves both, `implied.first_session_of_month` and
`baselines.Har.refit_day` must give the same refit day for every month of the committed calendar."""

from datetime import date, timedelta
from pathlib import Path

from fno.forecast_v4.sessions import is_scored_session
from fno.forecast_v4_rules.baselines import Har
from fno.forecast_v4_rules.implied import first_session_of_month
from fno.research_data.calendar import load_session_calendar

ROOT = Path(__file__).resolve().parents[2]
CALENDAR = load_session_calendar(ROOT / "research" / "data" / "calendar" / "nse_sessions.csv")


def test_both_refit_rules_give_the_same_day_for_every_month_of_the_calendar():
    days = [CALENDAR.first + timedelta(n) for n in range((CALENDAR.last - CALENDAR.first).days + 1)]
    sessions = [d for d in days if is_scored_session(CALENDAR, d)]
    har = Har([], 5, sessions)
    months = sorted({(d.year, d.month) for d in sessions})
    assert len(months) == 12 * (CALENDAR.last.year - CALENDAR.first.year + 1)
    for year, month in months:
        day = date(year, month, 15)
        assert first_session_of_month(day, sessions) == har.refit_day(day), (year, month)
