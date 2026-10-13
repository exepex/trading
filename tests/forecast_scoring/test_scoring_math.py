"""Story G4 criteria 1 and 2: known-answer scores with clipping; the block bootstrap reproduces committed values."""

from __future__ import annotations

import math

import numpy as np
import pytest

from fno.forecast_scoring.block_bootstrap import compare, holm_significant
from fno.forecast_scoring.scores import brier, calibration_bin, calibration_table, log_score, summarise

DIFFERENCES = [0.05 * math.sin(t) + 0.01 * (t % 3 - 1) for t in range(60)]  # 60 paired dates, fixture
COMMITTED = {
    "mean": 0.0016161160872767398,
    "p": 0.44815518448155184,
    "interval": (-0.002196496847533564, 0.0023129662470145616),
}  # comparison k = 11; fmt: skip


@pytest.mark.parametrize(
    ("p", "outcome", "brier_value", "log_value"),
    [
        (0.7, True, 0.09, -math.log(0.7)),
        (0.7, False, 0.49, -math.log(0.3)),
        (0.0, True, 1.0, -math.log(0.01)),  # clipped to 0.01: 4.60517...
        (1.0, False, 1.0, -math.log(0.01)),  # clipped to 0.99
        (0.995, True, 0.000025, -math.log(0.99)),  # clipped down
        (0.5, True, 0.25, math.log(2)),
    ],
)
def test_brier_and_clipped_log_score_match_hand_values(p, outcome, brier_value, log_value):
    assert brier(p, outcome) == pytest.approx(brier_value, abs=1e-12)
    assert log_score(p, outcome) == pytest.approx(log_value, abs=1e-12)


def test_calibration_has_ten_fixed_bins_and_one_falls_in_the_last():
    assert [calibration_bin(p) for p in (0.0, 0.0999, 0.1, 0.55, 0.9, 1.0)] == [0, 0, 1, 5, 9, 9]
    table = calibration_table([(0.05, False), (0.08, True), (0.95, True), (1.0, True)])
    assert len(table) == 10 and (table[0].low, table[9].high) == (0.0, 1.0)
    assert (table[0].count, table[0].mean_forecast, table[0].observed_frequency) == (2, pytest.approx(0.065), 0.5)
    assert (table[9].count, table[9].observed_frequency) == (2, 1.0) and table[4].mean_forecast is None


def test_summary_means_by_hand():
    s = summarise([(0.7, True), (0.2, False)])
    assert s.scored == 2 and s.mean_brier == pytest.approx((0.09 + 0.04) / 2)
    assert s.mean_log_score == pytest.approx((-math.log(0.7) - math.log(0.8)) / 2)


def independent_bootstrap(differences, k):
    """Protocol section 8 written out with loops (same seeding and draw shape, nothing shared with the module)."""
    n, length, resamples = len(differences), 20, 10_000
    blocks = math.ceil(n / length)
    starts = np.random.default_rng(np.random.SeedSequence([20261013, k])).integers(
        0, n - length + 1, (resamples, blocks)
    )
    means = []
    for row in starts:
        joined = [differences[s + j] for s in row for j in range(length)][:n]
        means.append(sum(joined) / n)
    observed = sum(differences) / n
    p = (1 + sum(abs(m - observed) >= abs(observed) for m in means)) / (resamples + 1)
    return observed, p, tuple(float(x) for x in np.percentile(means, (2.5, 97.5)))


def test_block_bootstrap_reproduces_the_committed_interval_exactly():
    result = compare(DIFFERENCES, 11)
    assert result.tested and result.n == 60
    assert result.mean_difference == pytest.approx(COMMITTED["mean"], abs=1e-15)
    assert result.p_value == COMMITTED["p"] and result.interval == COMMITTED["interval"]
    observed, p, interval = independent_bootstrap(DIFFERENCES, 11)
    assert observed == pytest.approx(result.mean_difference, abs=1e-15) and p == result.p_value
    assert interval == pytest.approx(result.interval, abs=1e-15)
    assert compare(DIFFERENCES, 12).interval != result.interval  # each comparison has its own seed


def test_fewer_than_40_paired_dates_are_not_tested():
    r = compare(DIFFERENCES[:39], 1)
    assert (r.tested, r.p_value, r.interval, r.n) == (False, 1.0, None, 39)
    assert compare([], 1).mean_difference is None


def test_holm_step_down_stops_at_the_first_failure():
    # thresholds over 4: 0.0125, 0.0167, 0.025, 0.05
    assert holm_significant([0.01, 0.04, 0.012, 0.03]) == [True, False, True, False]
    assert holm_significant([0.02, 0.001, 0.001, 0.001]) == [True, True, True, True]
    assert holm_significant([1.0] * 10) == [False] * 10
