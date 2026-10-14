"""Book 1, pure rules (story E5, design 12.1 and 12.9): each session day it decides by code alone. D2's evaluation of
its approved (`paper`) playbook versions, with C2 on Book 1's own account, written as D3's decision record (whose
`chosen_action` is the rule's action) and committed before E3's deadline. It has no AI authority: nothing on its path
calls or imports a model.

With no `paper` version on the day it also commits "no approved strategy": a result, not an error. D2 still runs, so
registered research candidates are forward-tested in shadow and the day's record exists for replay."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..constants import BOOK1_RULES, NO_APPROVED_STRATEGY
from ..desk.daily_ports import Committer
from ..playbook.allocation import StrategyTradeCounts
from ..playbook.decision_inputs import PlaybookSnapshot
from ..playbook.decision_run import DecisionRun
from ..playbook.decision_store import DecisionStore, DuplicateRun
from ..playbook.evaluate import LiveFeatureValues
from ..playbook.shadow import ShadowBooks
from ..research_data.calendar import SessionCalendar
from ..risk.inputs import Market, RiskBook

NO_APPROVED_FILE = "no_approved_strategy.json"
DECIDED = "Book 1 {day}: decided ({run}), committed {commit}"
ALREADY = "Book 1 {day}: these inputs were already decided ({reason})"
NOT_SESSION = "Book 1 {day}: not a session day, nothing decided"


@dataclass(frozen=True)
class Book1Day:
    """Everything D2 reads for Book 1 on a day, and the run's context (hashes and links, D3's RUN_CONTEXT)."""

    market: Market
    features: LiveFeatureValues
    book: RiskBook
    counts: StrategyTradeCounts
    shadow: ShadowBooks
    context: Mapping[str, object]


class Book1Inputs(ABC):
    @abstractmethod
    def day(self, day: date) -> Book1Day:
        """Book 1's inputs on the day, from the two packs, the canonical snapshot and its own account."""


class Book1:
    def __init__(self, root: Path, calendar: SessionCalendar, playbook: Callable[[], PlaybookSnapshot],
                 inputs: Book1Inputs, run: DecisionRun, committer: Committer):  # fmt: skip
        self.root, self.calendar, self.playbook, self.inputs, self.run, self.committer = (
            Path(root), calendar, playbook, inputs, run, committer)  # fmt: skip

    def decide(self, day: date) -> str:
        if not self.calendar.is_session(day):
            return NOT_SESSION.format(day=day)
        snapshot = self.playbook()
        paths = [] if snapshot.playbook().approved_on(day) else [self._no_approved(day, snapshot)]
        inputs = self.inputs.day(day)
        try:
            run = self.run.decide(day, snapshot, inputs.market, inputs.features, inputs.book, inputs.counts,
                                  inputs.shadow, inputs.context)  # fmt: skip
        except DuplicateRun as already:
            return ALREADY.format(day=day, reason=already)
        commit = self.committer.commit((run, *paths), f"Book 1 decision {day} ({run.name})")
        return DECIDED.format(day=day, run=run.name, commit=commit)

    def _no_approved(self, day: date, snapshot: PlaybookSnapshot) -> Path:
        path = DecisionStore(self.root, BOOK1_RULES).day_folder(day) / NO_APPROVED_FILE
        body = {"kind": NO_APPROVED_STRATEGY, "book": BOOK1_RULES, "day": day.isoformat(),
                "registry_commit": snapshot.commit}  # fmt: skip
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(body, sort_keys=True, indent=1) + "\n", encoding="utf-8")
        return path
