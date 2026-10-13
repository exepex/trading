"""Story G2 criteria 2 and 3: the statistical models' fit and probabilities by hand, and the fixed refit schedule."""

from datetime import date

import numpy
import pytest
from forecast_fixtures import DAYS, closes_history

from fno.forecast.models import MODEL_MINIMUM, MODEL_WINDOW, ModelBaseline, fit_ols, share


def test_ordinary_least_squares_by_hand():
    """y = 1 + 2x plus residuals (0.5, -1, 0.5), summing to 0 and orthogonal to x: the fit returns them exactly."""
    fit = fit_ols([(1.0,), (2.0,), (3.0,)], [3.5, 4.0, 7.5])
    assert fit.coefficients == pytest.approx([1.0, 2.0])
    assert fit.residuals == pytest.approx([0.5, -1.0, 0.5])
    predicted = fit.predict((2.5,)) + fit.residuals  # 6 + residuals = 6.5, 5.0, 6.5
    assert share(predicted, lambda v: v > 6.4) == pytest.approx(2 / 3)
    assert share(predicted, lambda v: v < 5.0) == 0.0  # strict


def test_the_window_and_minimum_are_the_protocols():
    assert (MODEL_WINDOW, MODEL_MINIMUM) == (750, 500)


def test_the_refit_day_is_the_first_trading_day_of_the_month():
    model = ModelBaseline(closes_history({}, count=40))
    assert model.refit_day(date(2026, 2, 20)) == date(2026, 2, 2)  # 1 Feb 2026 is a Sunday
    assert model.refit_day(date(2026, 1, 27)) == date(2026, 1, 1)


def test_too_few_rows_give_no_forecast():
    model = ModelBaseline(closes_history({}, count=60))
    assert model.probabilities(DAYS[59])["q3_rv20_above_trailing"] is None


def test_the_fit_is_shared_by_every_day_of_a_month():
    model = ModelBaseline(closes_history({i: 100.0 + (i % 3) for i in range(60)}, count=60), window=5, minimum=3)
    a, b = model.fit("q4_vix_up_10d", DAYS[45]), model.fit("q4_vix_up_10d", DAYS[50])
    assert model.refit_day(DAYS[45]) == model.refit_day(DAYS[50]) and a is b
    assert numpy.array_equal(a.coefficients, b.coefficients) if a is not None else b is None
