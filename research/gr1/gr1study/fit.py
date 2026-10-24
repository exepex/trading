"""Fitting one candidate on one cell's train rows (protocol section 5): the parameters `theta` that minimise the mean
quantile score, by a deterministic coordinate search (no scipy; no random state). Each coordinate tries +-step from
0, step halving from 0.5 to 2^-12. A parameter at the bound |theta| = 3 (a scale of e^3) is a grid-edge hit and a
failed fit (section 13); so is any quantile crossing on a scored day (C2's guard, judge 428.1)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .candidates import Candidate
from .rows import Row
from .scaling import crosses, quantile_score, rescaled

BOUND, FIRST_STEP, LAST_STEP = 3.0, 0.5, 2.0**-12
FAILED_EDGE, FAILED_CROSSING, FAILED_NO_ROWS = "grid edge hit", "quantiles cross", "no rows"


@dataclass(frozen=True)
class Fit:
    theta: tuple[float, ...] | None
    failed: str | None = None


def scaled(candidate: Candidate, theta: Sequence[float], row: Row, x: Sequence[float]) -> tuple[float, ...]:
    inner_x, outer_x = candidate.bands(x)
    inner = math.exp(sum(t * v for t, v in zip(theta, inner_x, strict=True)))
    outer = math.exp(sum(t * v for t, v in zip(theta, outer_x, strict=True)))
    return rescaled(row.quantiles, inner, outer)


def mean_score(candidate: Candidate, theta: Sequence[float], data: Sequence[tuple[Row, Sequence[float]]]) -> float:
    total = 0.0
    for row, x in data:
        quantiles = scaled(candidate, theta, row, x)
        if crosses(quantiles):
            return math.inf
        total += quantile_score(quantiles, row.outcome)
    return total / len(data)


def fit(candidate: Candidate, data: Sequence[tuple[Row, Sequence[float]]]) -> Fit:
    """`data`: the train rows with their conditioner vectors (rows without one already dropped)."""
    if not data:
        return Fit(None, FAILED_NO_ROWS)
    theta = [0.0] * candidate.parameters(data[0][1])
    best, step = mean_score(candidate, theta, data), FIRST_STEP
    while step >= LAST_STEP:
        improved = False
        for i in range(len(theta)):
            for move in (step, -step):
                trial = theta.copy()
                trial[i] = max(-BOUND, min(BOUND, trial[i] + move))
                score = mean_score(candidate, trial, data)
                if score < best:
                    theta, best, improved = trial, score, True
        if not improved:
            step /= 2
    if any(abs(t) >= BOUND for t in theta):
        return Fit(tuple(theta), FAILED_EDGE)
    return Fit(tuple(theta))


def crossing_on(candidate: Candidate, theta: Sequence[float], data: Sequence[tuple[Row, Sequence[float]]]) -> bool:
    """Judge 428.1: a crossing on any scored day (select or final) is a failed fit too."""
    return any(crosses(scaled(candidate, theta, row, x)) for row, x in data)
