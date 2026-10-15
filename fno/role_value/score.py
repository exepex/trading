"""One unit's score over a period (story F9a; S1 `role_value_minimum_sample`). Applicable opportunities are the scored
pairs on days the unit was ablated and its card consulted; the paired difference is with the unit minus without it (0
when the two decisions agree). The net value per opportunity is that difference minus the unit's cost per opportunity.
The bootstrap is S3's moving-block resampler (`fno/scoreboard/uncertainty.py`, imported) on the net values in date
order with a risk of 1 each, so its ratio is the mean: blocks of 20 opportunities, 10,000 resamples, seed 20261014.
Its 5th and 95th nearest-rank percentiles are printed only; the verdict comes from Holm on its one-sided p-values.
The risk effects (worst month, maximum loss) are printed beside the verdict and never decide it (owner, 15 Oct 2026:
"money only, risk shown")."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from ..scoreboard.series import DailySeries
from ..scoreboard.uncertainty import p_value, resampled_ratios

LOWER_PERCENTILE, UPPER_PERCENTILE = 5, 95  # provisional, to confirm at the S1 freeze (response 166, question 1)


@dataclass(frozen=True)
class Opportunity:
    day: date
    difference: float
    changed: bool
    max_loss_difference: float


@dataclass(frozen=True)
class UnitScore:
    unit: str
    applicable: int
    changed: int
    mean_difference: float | None
    cost: float | None  # rupees per opportunity; None: unknown
    mean_net_value: float | None
    interval: tuple[float, float] | None  # printed only
    p_earns: float | None  # one-sided: "net value above zero"
    p_drop: float | None  # one-sided: "net value below zero"
    worst_month: tuple[str, float] | None
    mean_max_loss_difference: float | None  # over changed opportunities


def _series(days: Sequence[date], values: Sequence[float]) -> DailySeries:
    return DailySeries(tuple(days), tuple(values), tuple(1.0 for _ in values))


def percentile(sorted_values: Sequence[float], p: int) -> float:
    return sorted_values[max(math.ceil(p / 100 * len(sorted_values)) - 1, 0)]


def worst_month(opportunities: Sequence[Opportunity]) -> tuple[str, float] | None:
    months: dict[str, float] = {}
    for o in opportunities:
        months[o.day.strftime("%Y-%m")] = months.get(o.day.strftime("%Y-%m"), 0.0) + o.difference
    return min(((m, round(v, 2)) for m, v in months.items()), key=lambda mv: (mv[1], mv[0])) if months else None


def score_unit(unit: str, opportunities: Sequence[Opportunity], cost: float | None) -> UnitScore:
    found = sorted(opportunities, key=lambda o: o.day)
    n, changed = len(found), [o for o in found if o.changed]
    mean = round(sum(o.difference for o in found) / n, 2) if n else None
    risk = round(sum(o.max_loss_difference for o in changed) / len(changed), 2) if changed else None
    if cost is None or not n:
        return UnitScore(unit, n, len(changed), mean, cost, None, None, None, None, worst_month(found), risk)
    values = [o.difference - cost for o in found]
    days = [o.day for o in found]
    ratios = resampled_ratios(_series(days, values))
    interval = None if ratios is None else (percentile(ratios, LOWER_PERCENTILE), percentile(ratios, UPPER_PERCENTILE))
    return UnitScore(
        unit, n, len(changed), mean, cost, round(sum(values) / n, 2),
        None if interval is None else (round(interval[0], 2), round(interval[1], 2)),
        p_value(_series(days, values)), p_value(_series(days, [-v for v in values])), worst_month(found), risk,
    )  # fmt: skip
