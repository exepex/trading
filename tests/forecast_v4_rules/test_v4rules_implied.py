"""Story G7b completion, part b1, criteria 1-5: the EOD IV30 proxy, raw implied, the premium ratio and
premium-adjusted implied (PROTOCOL_v4.md section 3.1), on hand-computed values and the committed NSE calendar."""

import math
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from fno.forecast_v4_rules.baselines import MISSING, NOT_ELIGIBLE, OK
from fno.forecast_v4_rules.eod_iv30 import eod_iv30_series
from fno.forecast_v4_rules.implied import (
    HorizonRv,
    ImpliedBaselines,
    IvPoint,
    PremiumRatio,
    first_session_of_month,
    horizon_sums,
    raw_implied,
)
from fno.forecast_v4_rules.series import DayValue
from fno.research_data.calendar import load_session_calendar

ROOT = Path(__file__).resolve().parents[2]
CALENDAR = load_session_calendar(ROOT / "research" / "data" / "calendar" / "nse_sessions.csv")
SESSIONS = [date(2026, 1, 1) + timedelta(n) for n in range(365)]
SESSIONS = [d for d in SESSIONS if CALENDAR.session_kind(d) == "regular"]
UNIT_IV = math.sqrt(365)  # with a one-day horizon, raw_h(t) = 1, so each window point's ratio is its RV
START = date(2024, 1, 1)


def unit_points(count: int, start: date = START, rv=lambda i: 1.0, flagged=lambda i: False):
    """`count` consecutive days from `start`, each resolving the next day, ratio = `rv(i)`."""
    days = [start + timedelta(i) for i in range(count)]
    eod = {d: IvPoint(UNIT_IV, flagged(i)) for i, d in enumerate(days)}
    outcomes = {d: HorizonRv(rv(i), d + timedelta(1)) for i, d in enumerate(days)}
    return eod, outcomes, days


def test_raw_implied_is_iv_squared_times_calendar_days_over_365():
    assert raw_implied(0.138, 7) == pytest.approx(0.138**2 * 7 / 365)  # 0.000365, the golden example's
    assert raw_implied(0.138, 7) == pytest.approx(0.00036523, rel=1e-5)


def test_raw_counts_calendar_days_to_the_hth_scored_session_across_a_holiday():
    # Fri 16 Oct 2026, h = 5: 19, 21, 22, 23, 26 Oct (20 Oct Dussehra); d+5 = Mon 26 Oct, 10 calendar days.
    implied = ImpliedBaselines(5, SESSIONS, PremiumRatio({}, {}))
    value = implied.raw(date(2026, 10, 16), IvPoint(0.15, False))
    assert value.status == OK and value.value == pytest.approx(0.15**2 * 10 / 365)
    # h = 20 from Fri 16 Oct: the 20th session is 17 Nov (holidays 20 Oct, 10 Nov; the 8 Nov muhurat not counted).
    implied20 = ImpliedBaselines(20, SESSIONS, PremiumRatio({}, {}))
    assert implied20.raw(date(2026, 10, 16), IvPoint(0.15, False)).value == pytest.approx(0.15**2 * 32 / 365)


def test_raw_is_missing_when_flagged_absent_zero_or_past_the_calendar():
    implied = ImpliedBaselines(5, SESSIONS, PremiumRatio({}, {}))
    assert implied.raw(date(2026, 10, 16), IvPoint(0.15, True)).status == MISSING
    assert implied.raw(date(2026, 10, 16), None).status == MISSING
    assert implied.raw(date(2026, 10, 16), IvPoint(0.0, False)).status == MISSING
    assert implied.raw(SESSIONS[-3], IvPoint(0.15, False)).status == MISSING  # only 2 sessions left in the list


def test_horizon_sums_add_the_next_h_session_variances_and_resolve_at_the_last():
    rv = [DayValue(date(2026, 10, d), v) for d, v in ((12, 1.0), (13, 2.0), (14, 3.0), (15, 4.0))]
    sums = horizon_sums(rv, 2)
    assert sums == {date(2026, 10, 12): HorizonRv(5.0, date(2026, 10, 14)),
                    date(2026, 10, 13): HorizonRv(7.0, date(2026, 10, 15))}  # fmt: skip
    assert horizon_sums([], 5) == {}


def test_ratio_needs_500_points_and_takes_their_median():
    refit = START + timedelta(600)
    eod, outcomes, _ = unit_points(499)
    assert PremiumRatio(eod, outcomes).at(refit) is None
    eod, outcomes, _ = unit_points(500, rv=lambda i: 10.0 if i < 200 else 1.0)  # mean 4.6, median 1.0
    assert PremiumRatio(eod, outcomes).at(refit) == pytest.approx(1.0)


def test_ratio_keeps_the_latest_750_points():
    eod, outcomes, _ = unit_points(1000, rv=lambda i: 9.0 if i < 250 else 2.0)
    assert PremiumRatio(eod, outcomes).at(START + timedelta(2000)) == pytest.approx(2.0)


def test_a_point_resolving_on_the_refit_day_is_out_and_the_day_before_is_in():
    eod, outcomes, days = unit_points(501, rv=lambda i: 3.0 if i == 500 else 1.0)
    last = days[-1]  # resolves the day after `last`
    ratio = PremiumRatio(eod, outcomes)
    assert ratio.at(last + timedelta(1)) == pytest.approx(1.0)  # resolves on the refit day: 500 points, all 1.0
    eod, outcomes, days = unit_points(501, rv=lambda i: 3.0 if i >= 250 else 1.0)  # 251 of 501 are 3.0
    ratio = PremiumRatio(eod, outcomes)
    assert ratio.at(days[-1] + timedelta(2)) == pytest.approx(3.0)  # all 501 in: the median is 3.0
    assert ratio.at(days[-1] + timedelta(1)) == pytest.approx(2.0)  # 500 in: median of 250 x 1.0 and 250 x 3.0


def test_flagged_days_and_days_before_2024_are_never_window_points():
    eod, outcomes, _ = unit_points(510, flagged=lambda i: i < 20)
    assert PremiumRatio(eod, outcomes).at(START + timedelta(600)) is None  # 490 unflagged
    eod, outcomes, _ = unit_points(510, start=date(2023, 12, 22))  # 10 days of 2023
    assert PremiumRatio(eod, outcomes).at(START + timedelta(600)) == pytest.approx(1.0)
    eod, outcomes, _ = unit_points(505, start=date(2023, 12, 22))  # 495 days from 2024
    assert PremiumRatio(eod, outcomes).at(START + timedelta(600)) is None


def test_premium_adjusted_is_raw_times_the_months_refit_ratio():
    eod, outcomes, _ = unit_points(600, rv=lambda i: 0.5)
    implied = ImpliedBaselines(5, SESSIONS, PremiumRatio(eod, outcomes))
    value = implied.premium_adjusted(date(2026, 10, 16), IvPoint(0.15, False))
    assert value.status == OK and value.value == pytest.approx(0.5 * 0.15**2 * 10 / 365)


def test_the_ratio_is_fixed_for_the_month_at_its_first_session():
    # On 1 Oct 2026 the window holds 250 points of 1.0 and 250 of 3.0 (median 2.0). A point of 3.0 resolving on
    # 5 Oct would make it 3.0 if the ratio were refit later in the month; October keeps 2.0.
    eod, outcomes, _ = unit_points(500, rv=lambda i: 1.0 if i % 2 else 3.0)
    eod[date(2026, 10, 2)] = IvPoint(UNIT_IV, False)
    outcomes[date(2026, 10, 2)] = HorizonRv(3.0, date(2026, 10, 5))
    implied = ImpliedBaselines(1, SESSIONS, PremiumRatio(eod, outcomes))
    assert first_session_of_month(date(2026, 10, 16), SESSIONS) == date(2026, 10, 1)
    # h = 1 from Fri 16 Oct: Mon 19 Oct, 3 calendar days
    value = implied.premium_adjusted(date(2026, 10, 16), IvPoint(0.15, False)).value
    assert value == pytest.approx(2.0 * 0.15**2 * 3 / 365)


def test_premium_adjusted_is_missing_without_raw_and_not_eligible_without_a_ratio():
    implied = ImpliedBaselines(5, SESSIONS, PremiumRatio({}, {}))
    assert implied.premium_adjusted(date(2026, 10, 16), IvPoint(0.15, True)).status == MISSING
    assert implied.premium_adjusted(date(2026, 10, 16), IvPoint(0.15, False)).status == NOT_ELIGIBLE


def test_eod_series_converts_points_keeps_flags_and_drops_2023_and_absent_days():
    answers = {date(2023, 12, 29): (14.0, False), date(2024, 1, 1): (13.8, False), date(2024, 1, 2): (15.0, True)}
    estimate = lambda d: SimpleNamespace(points=answers[d][0], flagged=answers[d][1]) if d in answers else None  # noqa: E731
    days = [date(2023, 12, 29), date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]
    assert eod_iv30_series(days, estimate) == {date(2024, 1, 1): IvPoint(0.138, False),
                                               date(2024, 1, 2): IvPoint(0.15, True)}  # fmt: skip
    assert eod_iv30_series([], estimate) == {}
