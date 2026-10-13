"""The frozen family of forecast comparisons (story G1 criterion 4; PROTOCOL.md section 8), in its numbered order.

For each question: the three book pairs, then each book against the question's first baseline, then against its
second. 5 x 9 = 45 comparisons, all in the family from the start (a comparison not yet possible has p = 1), adjusted
together by Holm's step-down at a family-wise error rate of 5%. Comparison k (1-based) seeds its bootstrap with
`SeedSequence([BOOTSTRAP_SEED, k])`.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from ..constants import (
    BASELINE_BASE_RATE,
    BASELINE_MODEL,
    BASELINE_RISK_NEUTRAL,
    BOOKS,
    FORECAST_Q1_UP_20D,
    FORECAST_Q2_MOVE_3PCT_20D,
    FORECAST_QUESTIONS,
)

BLOCK_LENGTH = 20  # trading days, moving-block bootstrap
RESAMPLES = 10_000
BOOTSTRAP_SEED = 20261013
FAMILY_ERROR_RATE = 0.05  # Holm's step-down over the whole family
MIN_PAIRED_DATES = 2 * BLOCK_LENGTH  # fewer: not tested, p = 1


@dataclass(frozen=True)
class Comparison:
    k: int  # 1-based position in the family: the bootstrap seed's second word
    question: str
    first: str  # D = Brier(first) - Brier(second); negative favours `first`
    second: str


def baselines_for(question: str) -> tuple[str, str]:
    """Questions 1-2: risk-neutral and base rate; questions 3-5: base rate and the statistical model."""
    if question in (FORECAST_Q1_UP_20D, FORECAST_Q2_MOVE_3PCT_20D):
        return BASELINE_RISK_NEUTRAL, BASELINE_BASE_RATE
    return BASELINE_BASE_RATE, BASELINE_MODEL


def comparison_family() -> tuple[Comparison, ...]:
    pairs = []
    for question in FORECAST_QUESTIONS:
        pairs += [(question, a, b) for a, b in combinations(BOOKS, 2)]
        pairs += [(question, book, baseline) for baseline in baselines_for(question) for book in BOOKS]
    return tuple(Comparison(k, q, a, b) for k, (q, a, b) in enumerate(pairs, start=1))
