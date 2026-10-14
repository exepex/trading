"""The confirmatory test of protocol v4 (PROTOCOL_v4.md section 5, revision 1 after ChatGPT review 99).

The centred moving-block bootstrap of revision 0 over-rejected true nulls in a seeded simulation (about 25% at a
nominal 5% with n = 2L, 6-13% at n = 125; `research/forecasts/v4_null_calibration.md`), so it is no longer
confirmatory. The confirmatory p is the larger of two studentized tests, so both must pass:

1. **Batch means t:** the most recent k x L pairs (k = floor(n / L), the earliest n - kL dropped) cut into k
   consecutive batches of L; t = mean / (SD of batch means / sqrt k); one-sided p = P(T_(k-1) <= t).
2. **Studentized moving-block bootstrap:** resamples as `bootstrap.block_indices` with seed words [BOOTSTRAP_SEED, k,
   2]; each resample's t* = (D*_b - D) / se*_b with se* from the same batch layout; p = (1 + #{t*_b <= t}) / (B + 1).
   A resample whose se* is 0 counts as no hit.

Fewer than 2L pairs, or a zero observed SE: not tested, p = 1.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from .bootstrap import OneSidedTest, block_indices
from .student_t import t_cdf
from .terms import BOOTSTRAP_SEED, RESAMPLES

STUDENTIZED_SEED_WORD = 2


def batch_layout(n: int, block: int) -> tuple[int, int]:
    """(first index used, number of batches)."""
    batches = n // block
    return n - batches * block, batches


def batch_standard_error(values: np.ndarray, block: int) -> np.ndarray:
    """SE of the mean from consecutive batch means along the last axis (works on one series or a resample matrix)."""
    first, batches = batch_layout(values.shape[-1], block)
    means = values[..., first:].reshape(*values.shape[:-1], batches, block).mean(axis=-1)
    return means.std(axis=-1, ddof=1) / math.sqrt(batches)


def batch_means_p(differences: Sequence[float], block: int) -> float:
    x = np.asarray(differences, dtype=float)
    if len(x) < 2 * block:
        return 1.0
    first, batches = batch_layout(len(x), block)
    se = float(batch_standard_error(x, block))
    if se == 0:
        return 1.0
    return t_cdf(float(x[first:].mean()) / se, batches - 1)


def studentized_bootstrap_p(differences: Sequence[float], block: int, k: int, resamples: int = RESAMPLES) -> float:
    x = np.asarray(differences, dtype=float)
    n = len(x)
    if n < 2 * block:
        return 1.0
    se = float(batch_standard_error(x, block))
    if se == 0:
        return 1.0
    observed = float(x.mean())
    sample = x[block_indices(n, block, [BOOTSTRAP_SEED, k, STUDENTIZED_SEED_WORD], resamples)]
    se_star = batch_standard_error(sample, block)
    valid = se_star > 0
    t_star = (sample.mean(axis=1)[valid] - observed) / se_star[valid]
    return (1 + int(np.count_nonzero(t_star <= observed / se))) / (resamples + 1)


def confirmatory_test(differences: Sequence[float], block: int, k: int, resamples: int = RESAMPLES) -> OneSidedTest:
    """p = max(batch means t, studentized block bootstrap): the member's p for Holm."""
    n = len(differences)
    mean = float(np.mean(differences)) if n else None
    if n < 2 * block:
        return OneSidedTest(n, mean, 1.0, False)
    p = max(batch_means_p(differences, block), studentized_bootstrap_p(differences, block, k, resamples))
    return OneSidedTest(n, mean, p, True)
