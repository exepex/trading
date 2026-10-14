"""A strategy version's statistical review (story E6, criteria 2 and 4; design 6 and 12.8): only on a review date of
its evaluation plan, and only once the paper gate is met (at least 20 completed positions and 3 months since the first
entry: a minimum, not proof). Open positions are never counted.

The rule (fixed here before any paper result exists; reasoning only, orchestrator default of 14 Oct 2026):
- sample: the C1 net of each completed position; its mean with a two-sided 95% interval from experiment 1's seeded
  bootstrap of the mean (`resampled_means`, nearest-rank 2.5% and 97.5% points);
- **retire** when the interval's upper end is below the plan's expected low (worse than planned, beyond doubt);
- **pause** when the mean is below the expected low but the interval still reaches it;
- **keep** otherwise;
- **promotable** to any real-money discussion only when the interval's lower end is above zero and the version's whole
  net, legging costs included, is positive; anything else is inconclusive and never promoted.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from ..constants import REVIEW_KEEP, REVIEW_PAUSE, REVIEW_RETIRE
from ..research_engine.statistics import resampled_means

MIN_POSITIONS, MIN_MONTHS = 20, 3  # design 6: the paper gate
RESAMPLES, SEED = 10_000, 20261014  # fixed before any paper result
TAILS = (0.025, 0.975)


@dataclass(frozen=True)
class Review:
    on: date
    review_date: bool
    positions: int
    months: int
    gate_met: bool
    mean_rs: float | None
    interval_rs: tuple[float, float] | None
    decision: str | None  # keep, pause or retire; None when nothing is decided today
    promotable: bool
    reason: str


def full_months(start: date, end: date) -> int:
    months = (end.year - start.year) * 12 + end.month - start.month
    return months - (end.day < start.day)


def interval(values: Sequence[float]) -> tuple[float, float]:
    means = resampled_means(values, RESAMPLES, SEED)
    return tuple(float(means[math.ceil(p * RESAMPLES) - 1]) for p in TAILS)


def decide(mean: float, low_high: tuple[float, float], expected_low: float) -> tuple[str, str]:
    low, high = low_high
    if high < expected_low:
        return REVIEW_RETIRE, f"the 95% interval's upper end Rs {high:,.2f} is below the expected low"
    if mean < expected_low:
        return REVIEW_PAUSE, f"mean Rs {mean:,.2f} is below the expected low; the interval still reaches it"
    return REVIEW_KEEP, f"mean Rs {mean:,.2f} is at or above the expected low Rs {expected_low:,.2f}"


def review(nets: Sequence[float], total_net: float, first_entry: date | None, plan: dict, on: date) -> Review:
    """`nets`: each completed position's C1 net; `total_net`: the version's whole net (legging costs included)."""
    review_date = on in plan["review_dates"]
    months = full_months(first_entry, on) if first_entry else 0
    gate = len(nets) >= MIN_POSITIONS and months >= MIN_MONTHS
    mean = sum(nets) / len(nets) if nets else None
    bounds = interval(nets) if len(nets) >= 2 else None
    shape = (on, review_date, len(nets), months, gate, mean, bounds)
    if not review_date:
        return Review(*shape, None, False, "not a review date of the plan: no statistical decision")
    if not gate:
        need = f"{len(nets)} of {MIN_POSITIONS} positions, {months} of {MIN_MONTHS} months"
        return Review(*shape, REVIEW_KEEP, False, f"keep: the gate is not met ({need}); not judged")
    decision, why = decide(mean, bounds, plan["expected_range"][0])
    promotable = bounds[0] > 0 and total_net > 0
    proof = "net profit shown" if promotable else "inconclusive: not promoted"
    return Review(*shape, decision, promotable, f"{decision}: {why}; {proof}")
