"""The books' committed decisions as the daily run sees them (story E3 with D3, judge 82). On time is what the collector
observes at the deadline: it pulls, and only runs visible in that commit count, whatever their committer clock says (a
run committed at 15:11:50 but pushed at 15:13 is late). The committer time before the deadline is the second check,
and D3's rule (committed before the execution snapshot started) the third, at the fill. The fills read only the runs
the decisions step recorded, by run ID and holding commit. Turning a run into entry orders is each book's part (E5, F5,
F6), behind `OrderBuilder`."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Protocol

from ..playbook.decision_store import SUMS_FILE, DecisionStore
from .daily_ports import CommittedDecision, DecisionSource, OrderBuilder
from .pack_items import available_time


class RunCommits(Protocol):
    def added_in(self, path: str) -> tuple[str, str] | None: ...

    def observed(self) -> str: ...


class RunNotRecorded(ValueError):
    """The run the decisions step recorded is gone or held by another commit: it is never filled."""


class D3CommittedDecisions(DecisionSource):
    def __init__(self, root: Path, git: RunCommits, orders: OrderBuilder):
        self.root, self.git, self.orders = Path(root), git, orders

    def observe(self) -> str:
        return self.git.observed()

    def committed(self, book: str, day: date, deadline: datetime) -> CommittedDecision | None:
        for run in reversed(DecisionStore(self.root, book).runs(day)):
            decision = self._decision(book, run)
            if decision is not None and decision.committed_at < deadline:
                return decision
        return None

    def recorded(self, book: str, day: date, run_id: str, commit: str) -> CommittedDecision:
        run = DecisionStore(self.root, book).day_folder(day) / run_id
        decision = self._decision(book, run) if run.is_dir() else None
        if decision is None or decision.commit != commit:
            raise RunNotRecorded(f"{book} {run_id}: not held by the recorded commit {commit}")
        return decision

    def _decision(self, book: str, run: Path) -> CommittedDecision | None:
        added = self.git.added_in((run / SUMS_FILE).relative_to(self.root).as_posix())
        moment = available_time(added[1]) if added else None
        if moment is None:
            return None
        return CommittedDecision(book, run.name, added[0], moment, tuple(self.orders.orders(book, run, moment)), run)
