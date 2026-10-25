"""Book 2's day sheet (story F5 part 1), E2e's `BookSheet` in the pack step: D2 over Book 2's tradable versions at
the cutoff, on Book 2's own account, from the snapshot the common pack names (never "the latest"). It goes into Book
2's private pack under "evaluation" (never a journal file: the private pack is kept in Drive). Book 2's session reads
it as its rule default; the decider gives it again from the same inputs and refuses the day when it differs."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import date

from ..books.book1 import Book1Day
from ..desk.book_sheet import BookSheet
from ..desk.common_pack import CommonPack
from ..playbook.decision_inputs import PlaybookSnapshot
from ..playbook.outcomes import DayEvaluation
from ..playbook.schema import version_id
from .evaluation import Book2Evaluators

SHEET_KIND, SHEET_SCHEMA = "book2_day_sheet", 1


def book2_snapshot(snapshot: PlaybookSnapshot, paused: Sequence[str]) -> PlaybookSnapshot:
    """The playbook as Book 2 reads it on the day: Book 1's files and registry, with Book 2's view and its pauses."""
    return PlaybookSnapshot(snapshot.files, snapshot.registry_csv, snapshot.commit, paused=tuple(sorted(paused)))


def day_sheet(day: date, evaluation: DayEvaluation, snapshot: PlaybookSnapshot) -> dict:
    """The rule default Book 2's AI chooses against: every book outcome with its built terms, the opportunities D2
    chose (each with its terms), the versions that reached C2, and each version's status (research or paper) and widths
    (what a `choose_width` may pick)."""
    playbook = snapshot.playbook()
    status = {version_id(*s.key): str(s.status) for s in playbook.strategies}
    widths = {version_id(*s.key): [float(w) for w in s.structure.widths] for s in playbook.strategies}
    opportunities, chosen = [], []
    for outcome in evaluation.outcomes:
        record = outcome.record()
        key = version_id(record["strategy"], record["version"])
        entry = {"opportunity_id": record["opportunity_id"], "version": key, "strategy_status": status.get(key, ""),
                 "widths": widths.get(key, []), "decision": record["decision"], "reason": record["reason"],
                 "trade": record["trade"]}  # fmt: skip
        opportunities.append(entry)
        if record["decision"] == "chosen":
            chosen.append({"opportunity_id": record["opportunity_id"], "version": key, "trade": record["trade"]})
    return {"kind": SHEET_KIND, "schema_version": SHEET_SCHEMA, "day": day.isoformat(),
            "playbook_commit": snapshot.commit, "paused": list(snapshot.paused or ()), "opportunities": opportunities,
            "rule_default": chosen, "eligible": sorted(version_id(*k) for k in evaluation.eligible)}  # fmt: skip


class Book2Sheet(BookSheet):
    def __init__(self, evaluators: Book2Evaluators, snapshot: Callable[[], PlaybookSnapshot],
                 paused: Callable[[date], Sequence[str]], inputs: Callable[[date, CommonPack], Book1Day]):  # fmt: skip
        """`inputs(day, common)`: D2's inputs at the cutoff from the pack's own snapshot and Book 2's account."""
        self.evaluators, self.snapshot, self.paused, self.inputs = evaluators, snapshot, paused, inputs

    def sheet(self, book: str, day: date, common: CommonPack) -> Mapping:
        snapshot = book2_snapshot(self.snapshot(), self.paused(day))
        today = self.inputs(day, common)
        evaluation = self.evaluators.rule_default().evaluate(day, snapshot.playbook(), today.market, today.features,
                                                              today.book, today.counts, today.shadow)  # fmt: skip
        return day_sheet(day, evaluation, snapshot)
