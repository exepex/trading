"""Stages 1-4 and the answer (PROTOCOL.md sections 8-9, amendment 1 sections A and C)."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import date

from .clusters import cluster_key, cluster_sizes, kish_count
from .evaluate import Outcome
from .rules import MIN_CLUSTERS_A_YEAR, MIN_FIT_SHARE, THIN_MARGIN_RATIO, clusters_a_year, clusters_a_year_needed

YES, NO, CANNOT = "YES", "NO", "CANNOT ANSWER"
STAGE_NAMES = {1: "cap", 2: "liquidity", 3: "cost wall", 4: "clusters"}


@dataclass(frozen=True)
class Scored:
    """One structure's outcome on one event, with the event's cluster."""

    outcome: Outcome
    reaction: date
    sector: str | None


@dataclass
class StructureResult:
    name: str
    events: int
    stage1_share: float
    stage2_share: float
    stage3_share: float | None = None
    median_net: float | None = None
    mean_net: float | None = None
    median_break_even: float | None = None
    median_gross_to_cost: float | None = None
    thin_margin: bool | None = None
    clusters: int | None = None
    clusters_a_year: float | None = None
    kish_passing: float | None = None
    untradable: dict = field(default_factory=dict)
    first_failed: str = ""

    def passes(self, stage: int) -> bool:
        if stage == 1:
            return self.stage1_share >= MIN_FIT_SHARE
        if stage == 2:
            return self.stage2_share >= MIN_FIT_SHARE
        if stage == 3:
            return bool(
                self.stage3_share is not None
                and self.stage3_share >= MIN_FIT_SHARE
                and (self.median_net or 0) > 0
                and (self.mean_net or 0) > 0
            )
        return (self.clusters_a_year or 0) >= MIN_CLUSTERS_A_YEAR


def share(flags: list[bool]) -> float:
    return sum(flags) / len(flags) if flags else 0.0


def median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def score_structure(
    name: str, scored: list[Scored], window: tuple[date, date], rho_abs: float | None
) -> StructureResult:
    """Every number of stages 1-4 for one structure on the decision window's events."""
    outcomes = [s.outcome for s in scored]
    untradable: dict[str, int] = {}
    for o in outcomes:
        if o.untradable:
            untradable[o.untradable] = untradable.get(o.untradable, 0) + 1
    result = StructureResult(
        name=name,
        events=len(outcomes),
        stage1_share=share([o.fits_without_pads for o in outcomes]),
        stage2_share=share([o.stage2 for o in outcomes]),
        untradable=untradable,
    )
    if any(o.expected_net is not None or o.bucket_untradable for o in outcomes):
        _cost_numbers(result, outcomes)
        passing = [s for s in scored if s.outcome.counts_for_clusters]
        keys = [cluster_key(s.sector, s.reaction) for s in passing]
        result.clusters = len(set(keys))
        result.clusters_a_year = clusters_a_year(result.clusters, *window)
        result.kish_passing = kish_count(cluster_sizes(keys), rho_abs)
    return result


def _cost_numbers(result: StructureResult, outcomes: list[Outcome]) -> None:
    fitting = [o for o in outcomes if o.stage3]
    nets = [o.expected_net for o in fitting]
    result.stage3_share = share([o.stage3 for o in outcomes])
    result.median_net = median(nets)
    result.mean_net = statistics.fmean(nets) if nets else None
    result.median_break_even = median([o.break_even_edge for o in fitting])
    ratios = [o.gross_to_cost for o in fitting if o.gross_to_cost is not None]
    result.median_gross_to_cost = median(ratios)
    result.thin_margin = (
        None if result.median_gross_to_cost is None else result.median_gross_to_cost < THIN_MARGIN_RATIO
    )


def decide(results: list[StructureResult], spreads_available: bool) -> dict:
    """The stage reached and the answer: stop at the first stage no structure passes."""
    for structure in results:
        structure.first_failed = next(
            (STAGE_NAMES[s] for s in range(1, 5) if (s < 3 or spreads_available) and not structure.passes(s)), ""
        )
    alive = results
    for stage in range(1, 5):
        if stage == 3 and not spreads_available:
            return {
                "answer": CANNOT,
                "stage": "stopped before stage 3",
                "reason": "cannot answer yet: no spread evidence",
            }
        alive = [r for r in alive if r.passes(stage)]
        if not alive:
            return {"answer": NO, "stage": f"stopped at stage {stage} ({STAGE_NAMES[stage]})", "reason": ""}
    power_need = clusters_a_year_needed(0.842)
    weak = [r.name for r in alive if (r.clusters_a_year or 0) < power_need]
    note = "YES under the registered rule; below the 80%-power need" if len(weak) == len(alive) else ""
    return {"answer": YES, "stage": "passed stage 4", "reason": note, "passing": [r.name for r in alive]}
