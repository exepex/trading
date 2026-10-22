"""GR1 protocol sections 5 and 8 on synthetic data: the rescaling keeps implied's median, the QS is G13b's (by hand),
coverage and widths in points, and the fit recovers a known scale, flags a grid-edge hit and refuses crossings."""

import math
from datetime import date

import pytest
from gr1study.candidates import SINGLE
from gr1study.evaluate import numbers, with_features
from gr1study.fit import BOUND, FAILED_EDGE, FAILED_NO_ROWS, crossing_on, fit, mean_score
from gr1study.scaling import INNER, OUTER, crosses, inside, quantile_score, rescaled, width_points

from tests.research_gr1.gr1_fakes import context, rows

Q = (-0.02, -0.01, 0.002, 0.012, 0.022)


def test_rescaling_keeps_the_median_and_scales_each_band_apart():
    out = rescaled(Q, 0.5, 2.0)
    assert out[2] == 0.002
    assert out[1] == pytest.approx(0.002 + 0.5 * (-0.012)) and out[3] == pytest.approx(0.002 + 0.5 * 0.010)
    assert out[0] == pytest.approx(0.002 + 2.0 * (-0.022)) and out[4] == pytest.approx(0.002 + 2.0 * 0.020)


def test_the_quantile_score_is_g13bs_by_hand():
    y = 0.015
    by_hand = 2 / 5 * sum((p - (y < q)) * (y - q) for p, q in zip((0.05, 0.25, 0.5, 0.75, 0.95), Q, strict=True))
    assert quantile_score(Q, y) == pytest.approx(by_hand)


def test_widths_are_in_points_and_crossing_is_detected():
    assert width_points(Q, 22_000.0, OUTER) == pytest.approx(22_000 * (math.exp(0.022) - math.exp(-0.02)))
    assert width_points(Q, 22_000.0, INNER) == pytest.approx(22_000 * (math.exp(0.012) - math.exp(-0.01)))
    assert not crosses(Q) and crosses((-0.02, -0.03, 0.0, 0.01, 0.02)) and crosses((0, 0, 0, 0, 0))


def test_c1_recovers_a_known_scale_and_c0_is_wider_than_the_truth():
    data = rows(date(2019, 1, 1), date(2023, 12, 31), implied_sd=0.01, true_sd=0.008)
    ctx = context()
    result = fit(SINGLE["C1"], with_features(SINGLE["C1"], data, ctx)[0])
    assert result.failed is None and math.exp(result.theta[0]) == pytest.approx(0.8, abs=0.04)
    c0, c1 = numbers(None, None, data, ctx), numbers(SINGLE["C1"], result.theta, data, ctx)
    assert c0.inside_90 > 0.95 and abs(c1.inside_90 - 0.90) < 0.03  # implied too wide; the scale calibrates it
    assert c1.mean_qs < c0.mean_qs and c1.width_90 < c0.width_90


def test_a_scale_beyond_the_bound_is_a_grid_edge_hit():
    data = rows(date(2019, 1, 1), date(2019, 12, 31), implied_sd=0.0001, true_sd=0.01)  # needs a scale of ~100
    result = fit(SINGLE["C1"], with_features(SINGLE["C1"], data, context())[0])
    assert result.failed == FAILED_EDGE and abs(result.theta[0]) == BOUND
    assert fit(SINGLE["C1"], []).failed == FAILED_NO_ROWS


def test_c2_never_fits_crossing_quantiles_and_a_crossing_on_any_scored_day_is_caught():
    data = with_features(SINGLE["C2"], rows(date(2019, 1, 1), date(2019, 6, 30)), context())[0]
    assert mean_score(SINGLE["C2"], (0.0, math.log(0.3)), data) == math.inf  # outer 0.3 x inner: q05 above q25
    result = fit(SINGLE["C2"], data)
    assert not crossing_on(SINGLE["C2"], result.theta, data)
    assert crossing_on(SINGLE["C2"], (0.0, math.log(0.3)), data)


def test_an_outcome_on_a_band_edge_is_inside():
    assert inside(Q, -0.02, OUTER) and inside(Q, 0.022, OUTER) and inside(Q, -0.01, INNER) and inside(Q, 0.012, INNER)
    assert not inside(Q, -0.0201, OUTER) and not inside(Q, 0.0121, INNER)
