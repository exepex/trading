"""Intervals (PROTOCOL.md sections 12 to 14): the stationary bootstrap (Politis and Romano) over sessions in date order,
and the cluster bootstrap over whole expiries for the flip share. B = 10,000, 95% percentile intervals. Each interval's
generator is seeded from the protocol's seed and the interval's name, so it does not depend on the order cells are
computed in, and the same run twice gives the same intervals."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

import numpy as np

SEED = 20261016
RESAMPLES = 10_000
BLOCKS = (5, 10, 20)  # mean block length in sessions; 5 is the one printed, 10 and 20 are checks
LOW, HIGH = 2.5, 97.5


def generator(name: str) -> np.random.Generator:
    digest = hashlib.sha256(f"{SEED}:{name}".encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


def stationary_indices(n: int, mean_block: int, rng: np.random.Generator, resamples: int = RESAMPLES) -> np.ndarray:
    """`resamples` x `n` indices: each step starts a new block with probability 1 / `mean_block`, otherwise takes the
    next session (wrapping round), so block lengths are geometric with that mean."""
    starts = rng.integers(0, n, size=(resamples, n))
    fresh = rng.random(size=(resamples, n)) < 1 / mean_block
    fresh[:, 0] = True
    picked = np.empty((resamples, n), dtype=np.int64)
    picked[:, 0] = starts[:, 0]
    for t in range(1, n):
        picked[:, t] = np.where(fresh[:, t], starts[:, t], (picked[:, t - 1] + 1) % n)
    return picked


def mean_interval(values: Sequence[float], mean_block: int, name: str) -> tuple[float, float]:
    """The 95% stationary-bootstrap interval of the mean of `values` (in date order)."""
    data = np.asarray(values, dtype=float)
    means = data[stationary_indices(len(data), mean_block, generator(f"{name}:block{mean_block}"))].mean(axis=1)
    low, high = np.percentile(means, [LOW, HIGH])
    return float(low), float(high)


def ratio_interval(numerators: Sequence[int], denominators: Sequence[int], name: str) -> tuple[float, float, int]:
    """The 95% interval of sum(numerators) / sum(denominators), resampling whole clusters with replacement; resamples
    with a zero denominator are dropped and their count returned."""
    top, bottom = np.asarray(numerators, dtype=float), np.asarray(denominators, dtype=float)
    picks = generator(name).integers(0, len(top), size=(RESAMPLES, len(top)))
    tops, bottoms = top[picks].sum(axis=1), bottom[picks].sum(axis=1)
    kept = bottoms > 0
    low, high = np.percentile(tops[kept] / bottoms[kept], [LOW, HIGH])
    return float(low), float(high), int((~kept).sum())
