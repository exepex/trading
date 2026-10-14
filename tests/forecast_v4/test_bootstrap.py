"""Story G6: the exact one-sided null-centred block bootstrap (seed, blocks, missing pairs, fewer than 2L pairs), the
minimum-effect gate on the RV > 0 set, the futility bound and the HAC sensitivity, against hand computations."""

from __future__ import annotations

import math

import numpy as np
import pytest

from fno.forecast_v4.bootstrap import (
    block_indices,
    effect_check,
    hac_one_sided_p,
    one_sided_test,
    relative_improvement,
)
from fno.forecast_v4.pairs import PairedSet
from fno.forecast_v4.terms import BOOTSTRAP_SEED

DIFFERENCES = [0.004 * math.sin(t) + 0.002 * (t % 3 - 1) - 0.0004 for t in range(60)]  # 60 paired dates, fixture
BASELINE = [0.02 + 0.005 * math.cos(t) for t in range(60)]
COMMITTED = {
    "mean": -0.000270710713017861,
    "p_block10_k4": 0.2672732726727327,
    "p_block5_k1": 0.28577142285771423,
    "hac_block10": 0.14204676552926243,
    "improvement": 0.013496327108828504,
    "upper_block10_k4": 0.039369083201854164,
}  # computed once at the protocol commit; any change to the rules changes them


def _by_hand(values: list[float], block: int, words: list[int], resamples: int) -> list[float]:
    """The protocol's words as a plain loop: ceil(n / L) starts from 0..n-L, blocks joined in draw order, cut to n."""
    n = len(values)
    blocks = math.ceil(n / block)
    starts = np.random.default_rng(np.random.SeedSequence(words)).integers(0, n - block + 1, size=(resamples, blocks))
    means = []
    for row in starts:
        joined = [values[s + i] for s in row for i in range(block)][:n]
        means.append(sum(joined) / n)
    return means


def test_p_value_is_one_plus_count_of_centred_means_at_or_below_d_over_b_plus_one():
    resamples = 499
    means = _by_hand(DIFFERENCES, 10, [BOOTSTRAP_SEED, 4], resamples)
    observed = sum(DIFFERENCES) / len(DIFFERENCES)
    expected = (1 + sum(m - observed <= observed for m in means)) / (resamples + 1)
    assert one_sided_test(DIFFERENCES, 10, 4, resamples).p_value == pytest.approx(expected, abs=1e-15)


def test_committed_values_reproduce_exactly():
    result = one_sided_test(DIFFERENCES, 10, 4)
    assert (result.n, result.tested) == (60, True)
    assert result.mean_difference == pytest.approx(COMMITTED["mean"], abs=1e-18)
    assert result.p_value == COMMITTED["p_block10_k4"]
    assert one_sided_test(DIFFERENCES, 5, 1).p_value == COMMITTED["p_block5_k1"]
    assert hac_one_sided_p(DIFFERENCES, 10) == pytest.approx(COMMITTED["hac_block10"], abs=1e-15)


def test_each_comparison_has_its_own_seed_word_and_reruns_are_identical():
    first, again = block_indices(60, 10, [BOOTSTRAP_SEED, 4]), block_indices(60, 10, [BOOTSTRAP_SEED, 4])
    assert np.array_equal(first, again)
    assert not np.array_equal(first, block_indices(60, 10, [BOOTSTRAP_SEED, 5]))
    assert first.shape == (10_000, 60) and first.min() == 0 and first.max() == 59


def test_blocks_are_contiguous_runs_of_length_l_cut_to_n():
    index = block_indices(23, 5, [BOOTSTRAP_SEED, 1], resamples=3)
    assert index.shape == (3, 23)
    for row in index:
        for start in range(0, 23, 5):
            run = row[start : start + 5]
            assert list(run) == list(range(run[0], run[0] + len(run)))


def test_fewer_than_two_blocks_of_pairs_is_not_tested_and_p_is_one():
    result = one_sided_test(DIFFERENCES[:19], 10, 1)
    assert (result.tested, result.p_value, result.n) == (False, 1.0, 19)
    assert one_sided_test(DIFFERENCES[:20], 10, 1).tested
    assert one_sided_test([], 10, 1).mean_difference is None


def test_direction_negative_mean_favours_the_forecaster():
    better = [d - 0.01 for d in DIFFERENCES]
    worse = [d + 0.01 for d in DIFFERENCES]
    assert one_sided_test(better, 10, 1).p_value < 0.001
    assert one_sided_test(worse, 10, 1).p_value > 0.999


def test_all_zero_differences_give_p_one():
    assert one_sided_test([0.0] * 40, 10, 1, resamples=99).p_value == 1.0


def test_gate_is_three_percent_of_the_baseline_mean_textbook_loss_on_the_same_dates():
    base = (2.0, 2.0, 2.0, 2.0)
    exactly = PairedSet((), (-0.06,) * 4, base)
    short = PairedSet((), (-0.058,) * 4, base)
    assert relative_improvement(exactly) == pytest.approx(0.03)
    assert effect_check(exactly, 0.03, 5, 1).meets_minimum_effect
    assert not effect_check(short, 0.03, 5, 1).meets_minimum_effect


def test_brier_gate_equals_a_brier_skill_score_of_two_percent():
    forecaster, baseline = [0.20, 0.10, 0.30], [0.25, 0.10, 0.30]
    gate = PairedSet((), tuple(f - b for f, b in zip(forecaster, baseline)), tuple(baseline))
    skill = 1 - sum(forecaster) / sum(baseline)
    assert relative_improvement(gate) == pytest.approx(skill)


def test_futility_bound_is_the_nearest_rank_95th_percentile_of_resampled_ratios():
    gate = PairedSet(tuple(range(60)), tuple(DIFFERENCES), tuple(BASELINE))
    check = effect_check(gate, 0.03, 10, 4)
    assert check.relative_improvement == pytest.approx(COMMITTED["improvement"], abs=1e-15)
    assert check.upper_bound == pytest.approx(COMMITTED["upper_block10_k4"], abs=1e-15)
    assert (check.meets_minimum_effect, check.futile) == (False, False)
    index = block_indices(60, 10, [BOOTSTRAP_SEED, 4, 1])
    d, b = np.asarray(DIFFERENCES)[index], np.asarray(BASELINE)[index]
    ratios = sorted(-d.sum(axis=1) / b.sum(axis=1))
    assert check.upper_bound == ratios[9_499]


def test_futile_when_improvement_is_surely_below_the_minimum_effect():
    tight = PairedSet(tuple(range(200)), tuple(-0.0002 + 0.0001 * math.sin(t) for t in range(200)), (0.05,) * 200)
    check = effect_check(tight, 0.03, 5, 1)
    assert check.relative_improvement == pytest.approx(0.004, abs=1e-3) and check.futile


def test_futility_is_never_declared_without_two_blocks_or_without_data():
    few = PairedSet(tuple(range(9)), (0.0,) * 9, (1.0,) * 9)
    assert effect_check(few, 0.03, 5, 1).futile is False and effect_check(few, 0.03, 5, 1).upper_bound is None
    assert effect_check(PairedSet((), (), ()), 0.03, 5, 1).futile is False


def test_hac_matches_a_hand_newey_west_and_is_none_when_undefined():
    x = [0.3, -0.1, 0.2, -0.4, 0.1, 0.0, -0.2, 0.5, -0.3, 0.1]
    n, lag = len(x), 4
    mean = sum(x) / n
    e = [v - mean for v in x]
    gamma = [sum(e[t] * e[t - j] for t in range(j, n)) / n for j in range(lag + 1)]
    variance = gamma[0] + 2 * sum((1 - j / (lag + 1)) * gamma[j] for j in range(1, lag + 1))
    expected = 0.5 * math.erfc(-(mean / math.sqrt(variance / n)) / math.sqrt(2))
    assert hac_one_sided_p(x, 5) == pytest.approx(expected, abs=1e-12)
    assert hac_one_sided_p(x[:9], 5) is None
    assert hac_one_sided_p([0.1] * 10, 5) is None
