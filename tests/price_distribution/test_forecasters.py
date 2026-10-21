"""G13 criterion 6: the forecasters and horizons. `implied` reads its expiry or scales the shortest usable one around
its median; `rv20` and `hist750` match hand values and say when they lack history; a holiday moves the target; the
calendar's end is not eligible."""

import math
from datetime import date, timedelta
from statistics import NormalDist

import numpy as np
import pytest

from fno.forecast_v4_rules.series import DayValue
from fno.price_distribution.chain import SpreadFilter
from fno.price_distribution.constants import E1, E2, FORECAST_LEVELS, H1, H5, MISSING, NOT_ELIGIBLE, OK
from fno.price_distribution.forecasters import (
    ForecastInputs,
    HistoricalForecaster,
    ImpliedForecaster,
    RealisedVolForecaster,
    realised_vol_points,
)
from fno.price_distribution.horizons import Target, targets
from fno.price_distribution.valuation import value_day
from fno.research_data.calendar import CsvSessionCalendar
from tests.price_distribution.builders import DAY, NEAR, NEXT, RATE, chain_day

CALENDAR = CsvSessionCalendar(
    "date,kind,description,source_url\n2026-10-20,holiday,Test holiday,https://example.invalid\n"
    "2026-12-25,holiday,Christmas,https://example.invalid\n"
)


def closes(n, start=date(2023, 1, 2), daily=0.01):
    """Closes alternating +daily/-daily in log: a hand-known RV and h-session returns."""
    out, level = [], 20_000.0
    for i in range(n):
        out.append(DayValue(start + timedelta(days=i), level))
        level *= math.exp(daily if i % 2 == 0 else -daily)
    return tuple(out)


HISTORY = closes(800)


def inputs(history=HISTORY, valuation=None, to_expiry=None, s_ref=22_990.0):
    return ForecastInputs(DAY, s_ref, valuation, history, to_expiry or {})


def test_a_holiday_inside_the_horizon_moves_the_target():
    found = targets(CALENDAR, DAY, [NEAR, NEXT])
    assert found[H1].day == date(2026, 10, 19)  # Friday 16 Oct -> Monday 19
    assert found[H5].day == date(2026, 10, 26)  # 19, 21, 22, 23, 26: the 20th is a holiday
    assert (found[E1].day, found[E1].sessions) == (NEAR, 6)
    assert (found[E2].day, found[E2].sessions) == (NEXT, 25)


def test_past_the_calendar_s_end_and_without_a_second_expiry_is_not_eligible():
    found = targets(CALENDAR, date(2026, 12, 31), [date(2027, 1, 28)])
    assert found[H1].day is None and "calendar ends" in found[H1].reason
    assert "calendar ends" in found[E1].reason and found[E2].reason == "no next expiry after the day in the chain"
    no_target = ImpliedForecaster().forecast(inputs(), found[E2])
    assert no_target.status == NOT_ELIGIBLE and no_target.reason == found[E2].reason


def test_implied_reads_its_expiry_and_scales_the_short_horizons_around_the_median():
    valuation = value_day(chain_day(), SpreadFilter(), RATE)
    near = next(e for e in valuation.usable() if e.expiry == NEAR)
    found = near.distribution.distribution
    e1 = ImpliedForecaster().forecast(inputs(valuation=valuation), Target(E1, NEAR, 6, NEAR))
    assert e1.status == OK
    assert e1.log_quantiles == pytest.approx([math.log(found.quantile(t)[0] / 22_990.0) for t in FORECAST_LEVELS])
    h5 = ImpliedForecaster().forecast(inputs(valuation=valuation, to_expiry={NEAR: 6, NEXT: 25}), Target(H5, DAY, 5))
    share, median = 5 / 6, math.log(found.quantile(0.5)[0] / near.forward)
    carry = math.log(near.forward / 22_990.0)
    expected = [share * (carry + median) + math.sqrt(share) * (math.log(found.quantile(t)[0] / near.forward) - median)
                for t in FORECAST_LEVELS]  # fmt: skip
    assert h5.log_quantiles == pytest.approx(expected)


def test_implied_without_a_long_enough_usable_expiry_is_missing():
    valuation = value_day(chain_day(), SpreadFilter(), RATE)
    found = ImpliedForecaster().forecast(inputs(valuation=valuation, to_expiry={NEAR: 3, NEXT: 4}), Target(H5, DAY, 5))
    assert found.status == MISSING and "at least 5 sessions" in found.reason
    gone = ImpliedForecaster().forecast(inputs(valuation=None), Target(E1, NEAR, 6, NEAR))
    assert gone.status == MISSING


def test_rv20_is_lognormal_at_the_last_20_returns_root_mean_square():
    found = RealisedVolForecaster().forecast(inputs(), Target(H5, DAY, 5))
    z = [NormalDist().inv_cdf(t) for t in FORECAST_LEVELS]
    assert found.log_quantiles == pytest.approx([v * 0.01 * math.sqrt(5) for v in z])
    assert realised_vol_points(HISTORY) == pytest.approx(0.01 * math.sqrt(252) * 100)


@pytest.mark.parametrize(("n", "status"), [(21, OK), (20, NOT_ELIGIBLE), (0, NOT_ELIGIBLE)])
def test_rv20_needs_21_closes(n, status):
    assert RealisedVolForecaster().forecast(inputs(closes(n)), Target(H1, DAY, 1)).status == status


def test_hist750_is_the_empirical_quantile_of_the_window_s_h_session_returns():
    history = tuple(DayValue(date(2023, 1, 1) + timedelta(days=i), 20_000 * math.exp(0.001 * i + 0.01 * math.sin(i)))
                    for i in range(900))  # fmt: skip
    window = history[-750:]
    returns = [math.log(b.value / a.value) for a, b in zip(window, window[5:], strict=False)]
    found = HistoricalForecaster().forecast(inputs(history), Target(H5, DAY, 5))
    assert found.log_quantiles == pytest.approx(list(np.quantile(returns, FORECAST_LEVELS)))


@pytest.mark.parametrize(("n", "status"), [(505, OK), (504, NOT_ELIGIBLE)])  # 500 five-session returns at 505 closes
def test_hist750_needs_500_returns(n, status):
    history = tuple(DayValue(date(2023, 1, 1) + timedelta(days=i), 20_000 * math.exp(0.01 * math.sin(i)))
                    for i in range(n))  # fmt: skip
    assert HistoricalForecaster().forecast(inputs(history), Target(H5, DAY, 5)).status == status


def test_tied_quantiles_are_refused_as_not_increasing():
    flat_history = tuple(DayValue(date(2023, 1, 1) + timedelta(days=i), 20_000.0) for i in range(800))
    found = HistoricalForecaster().forecast(inputs(flat_history), Target(H1, DAY, 1))
    assert found.status == MISSING and found.reason == "quantiles not strictly increasing"
