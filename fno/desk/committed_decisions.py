"""The books' committed decisions as the daily run sees them (story E3 with D3): a book's latest decision run whose
`records.sha256` was committed before the deadline. A run committed later is never read, so a slow book cannot join
late; D3's own rule (committed before the execution snapshot started) is checked again at the fill. Turning a run into
entry orders is each book's part (E5, F5, F6), behind `OrderBuilder`."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from ..playbook.decision_store import SUMS_FILE, DecisionStore
from ..playbook.decision_timing import CommitTimes
from .daily_ports import CommittedDecision, DecisionSource, OrderBuilder
from .pack_items import available_time


class D3CommittedDecisions(DecisionSource):
    def __init__(self, root: Path, git: CommitTimes, orders: OrderBuilder):
        self.root, self.git, self.orders = Path(root), git, orders

    def committed(self, book: str, day: date, deadline: datetime) -> CommittedDecision | None:
        for run in reversed(DecisionStore(self.root, book).runs(day)):
            added = self.git.added_at((run / SUMS_FILE).relative_to(self.root).as_posix())
            moment = available_time(added) if added else None
            if moment is not None and moment < deadline:
                return CommittedDecision(book, run.name, moment, tuple(self.orders.orders(book, run)))
        return None
