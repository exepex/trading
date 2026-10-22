"""The candidate form (protocol section 5) and the scores (section 8). Quantiles are log returns `ln(close / S_ref)`
at the levels 5, 25, 50, 75 and 95%; a candidate rescales implied's deviations from its own median, never the centre:
`q'_p = m + s (q_p - m)`, with one scale for the 25/75 band and one for the 5/95 band (equal unless C2)."""

from __future__ import annotations

import math
from collections.abc import Sequence

LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
OUTER, INNER, MEDIAN = (0, 4), (1, 3), 2


def rescaled(quantiles: Sequence[float], inner: float, outer: float) -> tuple[float, ...]:
    m = quantiles[MEDIAN]
    scale = (outer, inner, 1.0, inner, outer)
    return tuple(m + s * (q - m) for s, q in zip(scale, quantiles, strict=True))


def crosses(quantiles: Sequence[float]) -> bool:
    return any(b <= a for a, b in zip(quantiles, quantiles[1:], strict=False))


def pinball(level: float, outcome: float, quantile: float) -> float:
    return (level - (outcome < quantile)) * (outcome - quantile)


def quantile_score(quantiles: Sequence[float], outcome: float) -> float:
    """G13b's QS: (2/5) x the sum of the pinball losses, in log units."""
    return 2 / len(LEVELS) * sum(pinball(p, outcome, q) for p, q in zip(LEVELS, quantiles, strict=True))


def inside(quantiles: Sequence[float], outcome: float, band: tuple[int, int]) -> bool:
    return quantiles[band[0]] <= outcome <= quantiles[band[1]]


def width_points(quantiles: Sequence[float], s_ref: float, band: tuple[int, int]) -> float:
    return s_ref * (math.exp(quantiles[band[1]]) - math.exp(quantiles[band[0]]))


def median(values: Sequence[float]) -> float | None:
    ordered = sorted(values)
    n = len(ordered)
    if not n:
        return None
    return ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2
