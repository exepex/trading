"""Book 3's D2 evaluation (story F6): D2's own `RuleEvaluator` (opportunity windows, entry conditions on the live
15:00 features, candidates built on valid quotes, C2) over Book 3's tradable strategies, with the shared
`SelectionAllocator` holding the day's picks. The no-trade threshold is off: no Book 3 spec has a tested estimate.
Book 3 has no daily width or lots choice, so no `rebuild` is passed. The same evaluation, with no picks, is the day
sheet; with the picks it is the decision; rebuilt from a run's stored picks it is the replay behind orders."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..constants import BOOK3_AI
from ..playbook.allocation import Allocator
from ..playbook.candidates import CandidateBuilder
from ..playbook.evaluate import RuleEvaluator
from ..playbook.opportunities import OpportunityFinder
from ..playbook.outcomes import DayEvaluation
from ..playbook.schema import version_id
from ..playbook.selection import Pick, SelectionAllocator
from ..playbook.shadow import RealBooks

SHEET_KIND, SHEET_SCHEMA = "book3_day_sheet", 1


class Book3Evaluators:
    def __init__(self, finder: OpportunityFinder, builder: CandidateBuilder, allocator: Allocator, real: RealBooks):
        self.finder, self.builder, self.allocator, self.real = finder, builder, allocator, real

    def with_picks(self, picks: Sequence[Pick]) -> tuple[RuleEvaluator, SelectionAllocator]:
        selection = SelectionAllocator(self.allocator, picks, BOOK3_AI, threshold=False)
        return RuleEvaluator(self.finder, self.builder, selection, self.real), selection

    def from_stored(self, stored: Sequence[Mapping]) -> RuleEvaluator:
        """The evaluator a committed run was decided with, from the picks in its `inputs.json`."""
        return self.with_picks([Pick.from_json(p) for p in stored])[0]


def day_sheet(day: date, evaluation: DayEvaluation, commit: str) -> dict:
    """What Book 3's session sees of its own strategies today: each opportunity, whether its rule fired, and the trade
    built at the cutoff (or why none was), with nothing chosen."""
    opportunities = []
    for outcome in evaluation.outcomes:
        record = outcome.record()
        opportunities.append({
            "opportunity_id": record["opportunity_id"],
            "strategy_id": version_id(record["strategy"], record["version"]), "expiry": record["expiry"],
            "exit_day": record["exit_day"], "fired": not record["unmet_conditions"],
            "unmet_conditions": record["unmet_conditions"], "trade": record["trade"],
            "why_no_trade": "" if record["trade"] else record["reason"],
        })  # fmt: skip
    return {"kind": SHEET_KIND, "schema_version": SHEET_SCHEMA, "day": day.isoformat(), "strategies_commit": commit,
            "opportunities": opportunities}  # fmt: skip


def sheet_candidates(sheet: Mapping) -> set[str]:
    """The opportunity IDs with a built trade: the only ones Book 3 may pick."""
    return {o["opportunity_id"] for o in sheet["opportunities"] if o["trade"] is not None}
