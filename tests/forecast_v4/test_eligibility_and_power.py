"""Story G6: baseline eligibility (the predeclared primaries, V1's one-way HAR switch, never a stand-in) and the
60-outcome power report against design v2 section 5.5's arithmetic."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from fno.constants import (
    V1_RV_1S,
    V2_RV_5S,
    V3_RV_20S,
    V4_BASELINE_BASE_RATE,
    V4_BASELINE_HAR_DAILY,
    V4_BASELINE_HAR_INTRADAY,
    V4_BASELINE_OPTION_IMPLIED_PROB,
    V4_BASELINE_PREMIUM_ADJUSTED,
    V4_BASELINE_RAW_IMPLIED,
    V5_INSIDE_STRADDLE,
    V6_BIG_MOVE_1S,
    V6_BIG_MOVE_5S,
)
from fno.forecast_v4.eligibility import premium_ratio_window, primary_baseline
from fno.forecast_v4.power import power_report, required_outcomes
from fno.forecast_v4.terms import (
    FAMILY_SIZE,
    LOOK_ERROR_RATE,
    LOOK_SETTLE_DATE,
    LOOK_STOP_REVIEW,
    PRIMARY_BASELINE,
)

ALL = {
    V4_BASELINE_HAR_DAILY, V4_BASELINE_HAR_INTRADAY, V4_BASELINE_PREMIUM_ADJUSTED, V4_BASELINE_RAW_IMPLIED,
    V4_BASELINE_OPTION_IMPLIED_PROB, V4_BASELINE_BASE_RATE,
}  # fmt: skip


def test_primary_baselines_are_the_predeclared_ones():
    assert PRIMARY_BASELINE[V2_RV_5S] == PRIMARY_BASELINE[V3_RV_20S] == V4_BASELINE_PREMIUM_ADJUSTED
    assert PRIMARY_BASELINE[V5_INSIDE_STRADDLE] == V4_BASELINE_OPTION_IMPLIED_PROB
    assert primary_baseline(V2_RV_5S, ALL, False) == V4_BASELINE_PREMIUM_ADJUSTED


def test_an_ineligible_primary_leaves_the_pair_missing_never_filled_by_another_baseline():
    assert primary_baseline(V2_RV_5S, ALL - {V4_BASELINE_PREMIUM_ADJUSTED}, False) is None
    assert primary_baseline(V5_INSIDE_STRADDLE, {V4_BASELINE_BASE_RATE}, False) is None


def test_v1_uses_daily_har_until_intraday_har_is_eligible_and_never_switches_back():
    assert primary_baseline(V1_RV_1S, {V4_BASELINE_HAR_DAILY}, False) == V4_BASELINE_HAR_DAILY
    assert primary_baseline(V1_RV_1S, {V4_BASELINE_HAR_DAILY, V4_BASELINE_HAR_INTRADAY}, False) == (
        V4_BASELINE_HAR_INTRADAY
    )
    assert primary_baseline(V1_RV_1S, {V4_BASELINE_HAR_DAILY}, True) is None  # intraday went missing: no stand-in
    assert primary_baseline(V1_RV_1S, set(), False) is None


def _days(start: date, count: int) -> list[date]:
    return [start + timedelta(n) for n in range(count)]


def test_premium_ratio_window_uses_only_2024_onwards_and_needs_500_resolved_rows():
    refit = date(2026, 11, 2)
    rows = [(t, t + timedelta(7)) for t in _days(date(2023, 6, 1), 200) + _days(date(2024, 1, 1), 499)]
    assert premium_ratio_window(rows, refit) is None  # 499 from 2024: the 2023 rows never count
    rows.append((date(2025, 6, 1), date(2025, 6, 8)))
    window = premium_ratio_window(rows, refit)
    assert window is not None and len(window) == 500 and min(window) >= date(2024, 1, 1)


def test_premium_ratio_window_keeps_the_latest_750_resolved_before_the_refit():
    refit = date(2027, 1, 4)
    rows = [(t, t + timedelta(7)) for t in _days(date(2024, 1, 1), 1_000)]
    window = premium_ratio_window(rows, refit)
    resolved = [t for t, r in rows if r < refit]
    assert window == resolved[-750:] and all(t + timedelta(7) < refit for t in window)


def test_premium_ratio_window_refit_day_boundary_resolved_on_the_refit_day_is_left_out():
    refit = date(2026, 11, 2)
    rows = [(t, t + timedelta(7)) for t in _days(date(2024, 1, 1), 499)]
    on_refit, day_before = (date(2026, 10, 26), refit), (date(2026, 10, 25), refit - timedelta(1))
    assert premium_ratio_window([*rows, on_refit], refit) is None  # resolved == refit day: not known at its cutoff
    window = premium_ratio_window([*rows, day_before], refit)
    assert window is not None and window[-1] == date(2026, 10, 25)


def test_premium_ratio_window_first_day_is_1_jan_2024_inclusive():
    refit = date(2026, 11, 2)
    rows = [(t, t + timedelta(7)) for t in _days(date(2023, 12, 31), 501)]
    window = premium_ratio_window(rows, refit)
    assert window is not None and window[0] == date(2024, 1, 1) and len(window) == 500


@pytest.mark.parametrize(("r", "n"), [(3, 114), (5, 316), (10, 1_264)])
def test_design_table_is_reproduced_at_five_percent_over_fifteen(r, n):
    assert required_outcomes(r, 0.05, m=15) == n


@pytest.mark.parametrize(("look", "r", "n"), [(LOOK_STOP_REVIEW, 3, 134), (LOOK_SETTLE_DATE, 3, 125)])
def test_registered_looks_need_more_outcomes_than_a_single_five_percent_look(look, r, n):
    assert FAMILY_SIZE == 15
    assert required_outcomes(r, LOOK_ERROR_RATE[look]) == n


def test_the_power_report_waits_for_sixty_outcomes():
    with pytest.raises(ValueError, match="60 scored outcomes"):
        power_report(V6_BIG_MOVE_1S, [0.01, -0.01] * 29, 0.04, 0.02)


def test_power_report_measures_r_and_projects_the_remaining_years_honestly():
    differences = [0.0024, -0.0024] * 30  # SD 0.0024203; effect 0.02 x 0.04 = 0.0008: r = 3.0253
    daily = power_report(V6_BIG_MOVE_1S, differences, 0.04, 0.02)
    assert daily.r == pytest.approx(3.0253, abs=1e-4) and daily.n_required == 127
    assert daily.years_remaining == pytest.approx((127 - 60) / 252) and daily.useful
    five = power_report(V6_BIG_MOVE_5S, differences, 0.04, 0.02)
    assert five.years_remaining == pytest.approx((127 - 12) / 50.4) and not five.useful  # 60 overlapping = 12
