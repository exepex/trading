"""One candidate's numbers on one cell and period (protocol sections 7-8): its own days (paired with C0), the days it
drops and why, both coverages, both median widths in points, the mean QS and the daily QS differences against C0
in date order (for G4's bootstrap)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .candidates import Candidate, Context
from .fit import crossing_on, scaled
from .rows import Row
from .scaling import INNER, OUTER, inside, median, quantile_score, width_points

MISSING_INPUT = "an input of the day"


@dataclass(frozen=True)
class Numbers:
    days: int
    dropped: int
    inside_50: float | None
    inside_90: float | None
    width_50: float | None
    width_90: float | None
    mean_qs: float | None
    differences: tuple[float, ...]  # candidate QS minus C0 QS, date order
    crossed: bool
    needs: str = MISSING_INPUT  # what a dropped day lacks (judge 442 note 3)

    @property
    def dropped_reason(self) -> str | None:
        return self.needs if self.dropped else None

    @property
    def dropped_share(self) -> float:
        total = self.days + self.dropped
        return self.dropped / total if total else 0.0

    def as_dict(self) -> dict:
        mean_difference = sum(self.differences) / len(self.differences) if self.differences else None
        return {"days": self.days, "dropped": self.dropped, "dropped_reason": self.dropped_reason,
                "inside_25_75": self.inside_50, "inside_05_95": self.inside_90, "median_width_50_points": self.width_50,
                "median_width_90_points": self.width_90, "mean_qs": self.mean_qs,
                "mean_qs_difference_vs_c0": mean_difference, "crossed": self.crossed}  # fmt: skip


def with_features(candidate: Candidate, rows: Sequence[Row], ctx: Context) -> tuple[list, int]:
    """The rows that have the candidate's conditioners that day, and how many were dropped."""
    kept = [(row, x) for row in rows if (x := candidate.features(row, ctx)) is not None]
    return kept, len(rows) - len(kept)


def numbers(candidate: Candidate | None, theta, rows: Sequence[Row], ctx: Context) -> Numbers:
    """`candidate` None is C0 (implied unchanged)."""
    if candidate is None:
        data, dropped = [(row, None) for row in rows], 0
    else:
        data, dropped = with_features(candidate, rows, ctx)
    needs = (candidate.needs if candidate is not None else "") or MISSING_INPUT
    if not data:
        return Numbers(0, dropped, None, None, None, None, None, (), False, needs)
    quantiles = [row.quantiles if candidate is None else scaled(candidate, theta, row, x) for row, x in data]
    used = [row for row, _ in data]
    scores = [quantile_score(q, row.outcome) for q, row in zip(quantiles, used, strict=True)]
    base = [quantile_score(row.quantiles, row.outcome) for row in used]
    n = len(used)
    return Numbers(
        n, dropped,
        sum(inside(q, r.outcome, INNER) for q, r in zip(quantiles, used, strict=True)) / n,
        sum(inside(q, r.outcome, OUTER) for q, r in zip(quantiles, used, strict=True)) / n,
        median([width_points(q, r.s_ref, INNER) for q, r in zip(quantiles, used, strict=True)]),
        median([width_points(q, r.s_ref, OUTER) for q, r in zip(quantiles, used, strict=True)]),
        sum(scores) / n,
        tuple(s - b for s, b in zip(scores, base, strict=True)),
        candidate is not None and crossing_on(candidate, theta, data),
        needs,
    )  # fmt: skip
