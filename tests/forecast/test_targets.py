"""Story G1 criterion 1: each question's target against hand-worked values on fixture data, with a holiday and a
muhurat session inside the window.

Fixture calendar (2026): holidays on Mon 26 Jan and Tue 17 Feb, a muhurat session on Sun 22 Feb (not a trading day
for the targets). Forecast day d = Mon 2 Feb 2026.
- Counted by hand: 20 trading days before d is Fri 2 Jan (26 Jan skipped; 1 Jan is a regular day in this fixture);
  10 after is 16 Feb; 20 after is 3 Mar (17 Feb and the 22 Feb muhurat session skipped).
- NIFTY: from 2 Jan to d, daily log returns alternate +1%, -1% (20 returns): trailing RV = 1% x sqrt(252) = 15.8745.
  After d, 19 returns alternate +2%, -2% starting with +2%, then +4%: sum of squares 19 x 0.0004 + 0.0016 = 0.0092,
  next RV = sqrt(0.0092 / 20 x 252) = 34.0470 points; log change d to 3 Mar = +0.02 + 0.04 = 0.06, return e^0.06 - 1
  = 6.18%.
- India VIX: 15 on d, 16 on 16 Feb.
"""

import math
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from fno.constants import (
    FORECAST_Q1_UP_20D,
    FORECAST_Q2_MOVE_3PCT_20D,
    FORECAST_Q3_RV_RISES_20D,
    FORECAST_Q4_VIX_UP_10D,
    FORECAST_Q5_RV_BELOW_IV,
)
from fno.forecast.targets import DailyCloses, ForecastTargets, daily_closes, trading_days
from fno.research_data.calendar import CsvSessionCalendar

SOURCE = "https://example.invalid/circular"
CALENDAR = CsvSessionCalendar(
    "date,kind,description,source_url\n"
    f"2026-01-26,holiday,Republic Day,{SOURCE}\n"
    f"2026-02-17,holiday,Fixture holiday,{SOURCE}\n"
    f"2026-02-22,muhurat,Fixture muhurat,{SOURCE}\n"
)
D = date(2026, 2, 2)
START, END = date(2026, 1, 1), date(2026, 3, 31)


def _closes(days: tuple[date, ...], drop: date | None = None) -> list:
    """NIFTY and VIX closes as the module docstring describes; `drop` leaves one day's close out."""
    i_d, value, rows = days.index(D), 20000.0, []
    for i, day in enumerate(days):
        if 0 < i <= i_d:
            value *= math.exp(0.01 if (i_d - i) % 2 == 0 else -0.01)
        elif i > i_d:
            k = i - i_d
            value *= math.exp(0.04 if k == 20 else (0.02 if k % 2 == 1 else -0.02))
        vix = 16.0 if day == date(2026, 2, 16) else 15.0
        if day != drop:
            rows.append(SimpleNamespace(day=day, underlying=value, vix=vix))
    return rows


@pytest.fixture
def targets() -> ForecastTargets:
    days = trading_days(CALENDAR, START, END)
    return ForecastTargets(daily_closes(CALENDAR, START, END, _closes(days)))


def test_trading_days_skip_holidays_and_the_muhurat_session(targets):
    closes = targets.closes
    assert date(2026, 2, 17) not in closes.days and date(2026, 2, 22) not in closes.days
    assert closes.offset(D, -20) == date(2026, 1, 2)
    assert closes.offset(D, 10) == date(2026, 2, 16)
    assert closes.offset(D, 20) == date(2026, 3, 3)


def test_realised_volatilities_by_hand(targets):
    assert targets.trailing_rv(D) == pytest.approx(1.0 * math.sqrt(252), abs=1e-9)  # 15.8745
    assert targets.next_rv(D) == pytest.approx(math.sqrt(0.0092 / 20 * 252) * 100, abs=1e-9)  # 34.0470
    assert targets.next_rv(D) == pytest.approx(34.0470, abs=1e-4)


def test_the_five_outcomes_by_hand(targets):
    assert targets.outcome(FORECAST_Q1_UP_20D, D) is True  # +6.18%
    assert targets.outcome(FORECAST_Q2_MOVE_3PCT_20D, D) is True  # 6.18% >= 3%
    assert targets.outcome(FORECAST_Q3_RV_RISES_20D, D) is True  # 34.05 > 15.87
    assert targets.outcome(FORECAST_Q4_VIX_UP_10D, D) is True  # 16 > 15
    assert targets.outcome(FORECAST_Q5_RV_BELOW_IV, D, atm_iv30_points=40.0) is True  # 34.05 < 40
    assert targets.outcome(FORECAST_Q5_RV_BELOW_IV, D, atm_iv30_points=30.0) is False  # 34.05 >= 30


def _two_closes(first: float, last: float) -> ForecastTargets:
    days = tuple(date(2026, 1, 1) + timedelta(days=n) for n in range(21))
    nifty = {day: first for day in days} | {days[-1]: last}
    return ForecastTargets(DailyCloses(days, nifty, dict.fromkeys(days, 15.0)))


def test_an_unchanged_close_is_no_and_a_move_of_exactly_3pct_counts():
    assert _two_closes(100.0, 100.0).nifty_up(date(2026, 1, 1)) is False
    assert _two_closes(100.0, 97.0).nifty_moves_3pct(date(2026, 1, 1)) is True
    assert _two_closes(100.0, 102.99).nifty_moves_3pct(date(2026, 1, 1)) is False


def test_a_day_after_d_with_a_tie_in_vix_is_no(targets):
    """VIX 15 on 3 Feb and 15 on 17 Feb's next trading day 18 Feb (10 trading days later): equal, so no."""
    day = date(2026, 2, 3)
    assert targets.closes.offset(day, 10) == date(2026, 2, 18)
    assert targets.vix_up(day) is False


def test_a_missing_close_makes_the_outcome_void_never_a_guess():
    days = trading_days(CALENDAR, START, END)
    gap = ForecastTargets(daily_closes(CALENDAR, START, END, _closes(days, drop=date(2026, 2, 20))))
    assert gap.next_rv(D) is None and gap.rv_rises(D) is None and gap.rv_below_iv(D, 40.0) is None
    assert gap.nifty_up(D) is True  # questions 1 and 2 need only d and d+20


def test_a_target_beyond_the_data_or_a_non_trading_day_is_void(targets):
    late = targets.closes.days[-5]
    assert targets.nifty_up(late) is None and targets.vix_up(late) is None
    assert targets.nifty_up(date(2026, 2, 17)) is None  # a holiday is not a forecast day
    assert targets.rv_below_iv(D, None) is None  # no IV30 that day


def test_an_unknown_question_is_an_error(targets):
    with pytest.raises(ValueError, match="unknown"):
        targets.outcome("q6", D)


def test_daily_closes_keeps_calendar_days_without_a_close_as_missing():
    days = trading_days(CALENDAR, START, END)
    closes = daily_closes(CALENDAR, START, END, _closes(days, drop=D + timedelta(days=1)))
    assert closes.nifty[D + timedelta(days=1)] is None and D + timedelta(days=1) in closes.days
