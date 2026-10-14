"""Story G6: the QLIKE ranking loss at zero, near-zero and missing RV; its paired differences equal the textbook form's
when RV > 0; and the two frozen date sets (scored set with zeros, gate set with RV > 0 only) with their counts."""

from __future__ import annotations

import math
import random
from datetime import date, timedelta

import pytest

from fno.forecast_v4.loss import LossInputError, brier, ranking_qlike, textbook_qlike
from fno.forecast_v4.pairs import DatedForecasts, pair_point, pair_probability

DAY = date(2026, 11, 2)


def _day(n: int) -> date:
    return DAY + timedelta(n)


def test_ranking_loss_at_zero_rv_is_ln_f_and_rv_is_never_changed():
    assert ranking_qlike(0.0001, 0.0) == pytest.approx(math.log(0.0001), abs=1e-15)
    assert ranking_qlike(2.0, 0.0) == math.log(2.0)


def test_ranking_loss_near_zero_rv_is_finite_and_continuous():
    tiny = 1e-300
    assert math.isfinite(ranking_qlike(1e-6, tiny))
    assert ranking_qlike(1e-6, tiny) == pytest.approx(ranking_qlike(1e-6, 0.0), abs=1e-12)
    assert math.isfinite(textbook_qlike(1e-6, 1e-12))  # textbook form defined for any RV > 0


@pytest.mark.parametrize("forecast", [0.0, -1e-6, math.nan, math.inf])
def test_a_forecast_must_be_strictly_positive_and_finite(forecast):
    with pytest.raises(LossInputError):
        ranking_qlike(forecast, 0.0001)


@pytest.mark.parametrize("realised", [-1e-12, math.nan, math.inf])
def test_an_observed_rv_must_be_finite_and_not_negative(realised):
    with pytest.raises(LossInputError):
        ranking_qlike(0.0001, realised)


def test_textbook_form_is_refused_at_zero_rv():
    with pytest.raises(LossInputError, match="undefined at RV = 0"):
        textbook_qlike(0.0001, 0.0)


def test_paired_differences_are_equal_under_both_forms_whenever_rv_is_positive():
    rng = random.Random(6)
    for _ in range(2_000):
        rv = 10 ** rng.uniform(-9, -2)
        f, g = 10 ** rng.uniform(-7, -3), 10 ** rng.uniform(-7, -3)
        ranking = ranking_qlike(f, rv) - ranking_qlike(g, rv)
        textbook = textbook_qlike(f, rv) - textbook_qlike(g, rv)
        assert ranking == pytest.approx(textbook, rel=1e-9, abs=1e-9)
        assert ranking_qlike(f, rv) - textbook_qlike(f, rv) == pytest.approx(math.log(rv) + 1, rel=1e-12)


def test_brier_is_squared_error_and_refuses_values_outside_zero_one():
    assert brier(0.7, True) == pytest.approx(0.09) and brier(0.7, False) == pytest.approx(0.49)
    with pytest.raises(LossInputError):
        brier(1.01, True)


def test_scored_set_keeps_zero_rv_and_zero_differences_gate_set_leaves_zeros_out_and_counts_them():
    rows = [
        DatedForecasts(_day(0), 0.0001, 0.0002, 0.0),  # zero RV: scored, not in the gate
        DatedForecasts(_day(1), 0.0001, 0.0001, 0.00008),  # zero difference: stays in
        DatedForecasts(_day(2), 0.0002, 0.0001, 0.00015),
        DatedForecasts(_day(3), 0.0001, 0.0002, 0.0),  # second zero-RV date
    ]
    pairing = pair_point(rows)
    assert pairing.scored.days == tuple(_day(n) for n in range(4))
    assert pairing.gate.days == (_day(1), _day(2))
    assert pairing.zero_rv_left_out_of_gate == 2
    assert pairing.scored.differences[1] == 0.0
    assert pairing.scored.differences[0] == pytest.approx(math.log(0.0001) - math.log(0.0002))
    assert pairing.gate.baseline_losses[1] == pytest.approx(textbook_qlike(0.0001, 0.00015))


def test_missing_void_and_unresolved_dates_are_dropped_and_counted_never_imputed():
    rows = [
        DatedForecasts(_day(4), 0.0001, 0.0001, 0.0001),
        DatedForecasts(_day(0), None, 0.0001, 0.0001),  # forecaster missing
        DatedForecasts(_day(1), 0.0001, None, 0.0001),  # baseline missing or not eligible
        DatedForecasts(_day(2), 0.0001, 0.0001, 0.0001, void=True),
        DatedForecasts(_day(3), 0.0001, 0.0001, None),  # missing RV: unresolved
    ]
    pairing = pair_point(rows)
    assert pairing.scored.days == (_day(4),)
    counts = (pairing.missing_forecast, pairing.missing_baseline, pairing.void, pairing.unresolved)
    assert counts == (1, 1, 1, 1)


def test_rows_are_put_in_date_order_and_one_date_cannot_appear_twice():
    rows = [DatedForecasts(_day(n), 0.5, 0.4, n % 2 == 0) for n in (3, 1, 2)]
    assert pair_probability(rows).scored.days == (_day(1), _day(2), _day(3))
    with pytest.raises(ValueError, match="one row per date"):
        pair_probability([*rows, DatedForecasts(_day(1), 0.5, 0.4, True)])


def test_a_probability_question_uses_brier_and_its_gate_set_is_the_scored_set():
    rows = [DatedForecasts(_day(0), 0.9, 0.5, True), DatedForecasts(_day(1), 0.2, 0.5, False)]
    pairing = pair_probability(rows)
    assert pairing.gate == pairing.scored and pairing.zero_rv_left_out_of_gate == 0
    assert pairing.scored.differences == pytest.approx((0.01 - 0.25, 0.04 - 0.25))
    assert pairing.scored.baseline_losses == pytest.approx((0.25, 0.25))
