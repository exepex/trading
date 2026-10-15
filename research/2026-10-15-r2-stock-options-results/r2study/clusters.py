"""Effective independent clusters (PROTOCOL.md section 7, amendment 1 sections A and D9)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

import numpy as np

from .rules import BOOTSTRAP_INTERVAL, BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED, UNKNOWN_SECTOR


def cluster_key(sector: str | None, reaction: date) -> tuple[str, int, int]:
    """Sector x ISO year and week of the reaction session; a stock outside the sector list is `unknown`."""
    iso = reaction.isocalendar()
    return (sector or UNKNOWN_SECTOR, iso.year, iso.week)


def icc_anova(groups: list[list[float]]) -> float | None:
    """One-way ANOVA intra-cluster correlation with unequal sizes: (MSB - MSW) / (MSB + (n0 - 1) MSW),
    n0 = (N - sum n_c^2 / N) / (k - 1). None when it is not defined (fewer than 2 clusters, or no within-cluster
    degrees of freedom, or no variance)."""
    groups = [g for g in groups if g]
    k, n = len(groups), sum(len(g) for g in groups)
    if k < 2 or n - k < 1:
        return None
    grand = sum(sum(g) for g in groups) / n
    means = [sum(g) / len(g) for g in groups]
    ssb = sum(len(g) * (m - grand) ** 2 for g, m in zip(groups, means, strict=True))
    ssw = sum((x - m) ** 2 for g, m in zip(groups, means, strict=True) for x in g)
    msb, msw = ssb / (k - 1), ssw / (n - k)
    n0 = (n - sum(len(g) ** 2 for g in groups) / n) / (k - 1)
    denominator = msb + (n0 - 1) * msw
    return None if denominator == 0 else (msb - msw) / denominator


def bootstrap_interval(groups: list[list[float]]) -> tuple[float | None, float | None]:
    """Cluster bootstrap of the ICC: clusters drawn with replacement; the 5th and 95th percentiles."""
    groups = [g for g in groups if g]
    if len(groups) < 2:
        return None, None
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    values = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        drawn = rng.integers(0, len(groups), len(groups))
        rho = icc_anova([groups[i] for i in drawn])
        if rho is not None:
            values.append(rho)
    if not values:
        return None, None
    low, high = np.percentile(values, BOOTSTRAP_INTERVAL)
    return float(low), float(high)


def kish_count(sizes: list[int], rho: float | None) -> float:
    """Kish's effective count: the sum over clusters of n_c / (1 + (n_c - 1) max(rho, 0))."""
    r = max(rho or 0.0, 0.0)
    return sum(n / (1 + (n - 1) * r) for n in sizes if n > 0)


def cluster_sizes(keys: list[tuple]) -> list[int]:
    counts: dict[tuple, int] = defaultdict(int)
    for key in keys:
        counts[key] += 1
    return list(counts.values())


def grouped(values: list[tuple[tuple, float]]) -> list[list[float]]:
    """(cluster key, value) pairs as one list of values per cluster."""
    groups: dict[tuple, list[float]] = defaultdict(list)
    for key, value in values:
        groups[key].append(value)
    return list(groups.values())
