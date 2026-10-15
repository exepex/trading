"""Known-answer scores (story G8 criterion 2), by hand."""

import math

import pytest

from fno.forecast_scoring.v4.scores import least_squares, point_scores, probability_scores


def test_point_scores_by_hand_with_a_zero_rv_day():
    pairs = [(1e-4, 2e-4), (2e-4, 0.0), (4e-4, 4e-4)]
    s = point_scores(pairs)
    qlike = [math.log(1e-4) + 2, math.log(2e-4), math.log(4e-4) + 1]
    assert s.n == 3 and s.mean_qlike == pytest.approx(sum(qlike) / 3)
    textbook = [2 - math.log(2) - 1, 0.0]  # the zero-RV day is left out of the textbook mean
    assert s.mean_textbook_qlike == pytest.approx(sum(textbook) / 2)
    assert s.mean_squared_error == pytest.approx((1e-8 + 4e-8 + 0) / 3)
    a, b = least_squares([1e-4, 2e-4, 4e-4], [2e-4, 0.0, 4e-4])
    assert (
        (s.intercept, s.slope) == (a, b) and b == pytest.approx(6 / 7) and a == pytest.approx(0, abs=1e-18)
    )  # Sxy 4, Sxx 42/9 (x1e-8)


def test_probability_scores_by_hand():
    pairs = [(0.2, True), (0.2, False), (0.9, True), (0.05, False)]
    base = [(p, 0.25, o) for p, o in pairs]
    s = probability_scores(pairs, base)
    assert s.mean_brier == pytest.approx((0.64 + 0.04 + 0.01 + 0.0025) / 4)
    assert s.mean_log_score == pytest.approx(-(math.log(0.2) + math.log(0.8) + math.log(0.9) + math.log(0.95)) / 4)
    base_brier = (0.5625 + 0.0625 + 0.5625 + 0.0625) / 4
    assert s.brier_skill == pytest.approx(1 - s.mean_brier / base_brier)
    assert [b.count for b in s.calibration][:3] == [1, 0, 2] and s.calibration[9].count == 1
    assert (s.intercept, s.slope) == least_squares([0.2, 0.2, 0.9, 0.05], [1.0, 0.0, 1.0, 0.0])


def test_empty_and_flat_inputs():
    assert point_scores([]) is None and probability_scores([], []) is None
    assert least_squares([0.1, 0.1], [0.0, 1.0]) == (None, None)
    assert probability_scores([(0.1, True)], []).brier_skill is None


def test_the_skill_score_is_paired_and_reports_its_own_day_count():
    pairs = [(0.2, True), (0.2, False), (0.9, True)]  # three scored days of the forecaster
    base = [(0.2, 0.25, True), (0.9, 0.25, True)]  # the base rate exists on two of them only
    s = probability_scores(pairs, base)
    assert (s.n, s.skill_n) == (3, 2)
    assert s.brier_skill == pytest.approx(1 - ((0.64 + 0.01) / 2) / 0.5625)  # the two paired days only
