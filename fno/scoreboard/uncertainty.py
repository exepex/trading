"""S1's uncertainty criterion on scoreboard B (story S2): a one-sided lower bound of net per unit of risk from a moving-
block bootstrap over the daily (net change, risk at stake) pairs, the ratio of means recomputed on every resample, and
the sample a claim needs. The figures below are S1's PROPOSALS (`uncertainty_criterion`, `paper_gate`), not yet
decided by the owner: provisional, never frozen until S1's freeze. A test checks each against the protocol's text."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .series import DailySeries

BLOCK_DAYS = 20  # trading days, one holding period
RESAMPLES = 10_000
SEED = 20261014
LOWER_PERCENTILE = 5  # one-sided 95%, nearest rank
MIN_DAYS_SINCE_START = 120  # trading days since the common start
MIN_POSITIONS = 20  # completed positions (paper gate)
MIN_MONTHS = 3  # full calendar months (paper gate)
FIGURES_STATUS = "S1 proposal, provisional: not decided by the owner"


@dataclass(frozen=True)
class Uncertainty:
    lower_bound: float | None  # None when the series is shorter than one block or never at risk
    sample_met: bool
    claim_allowed: bool  # sample met, lower bound above zero and the whole period's net above zero
    reason: str


def lower_bound(series: DailySeries, seed: int = SEED, resamples: int = RESAMPLES) -> float | None:
    n = len(series.days)
    if n < BLOCK_DAYS or series.risk_days <= 0:
        return None
    rng, starts, ratios = random.Random(seed), n - BLOCK_DAYS + 1, []
    for _ in range(resamples):
        net = risk = 0.0
        taken = 0
        while taken < n:
            start = rng.randrange(starts)
            for i in range(start, start + min(BLOCK_DAYS, n - taken)):
                net, risk = net + series.net[i], risk + series.risk[i]
            taken += BLOCK_DAYS
        ratios.append(net / risk if risk > 0 else 0.0)  # a resample never at risk made nothing per unit of risk
    ratios.sort()
    return ratios[max(math.ceil(LOWER_PERCENTILE / 100 * resamples) - 1, 0)]


def uncertainty(series: DailySeries, positions: int, months: int) -> Uncertainty:
    sample = len(series.days) >= MIN_DAYS_SINCE_START and positions >= MIN_POSITIONS and months >= MIN_MONTHS
    bound = lower_bound(series)
    if not sample:
        why = (f"sample not met: {len(series.days)} of {MIN_DAYS_SINCE_START} trading days, {positions} of "
               f"{MIN_POSITIONS} completed positions, {months} of {MIN_MONTHS} full months")  # fmt: skip
        return Uncertainty(bound, False, False, why)
    allowed = bound is not None and bound > 0 and series.total_net > 0
    why = "lower bound and whole-period net above zero" if allowed else "lower bound or whole-period net not above zero"
    return Uncertainty(bound, True, allowed, why)
