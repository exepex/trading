"""What waits for an owner-timing fill (story E8 rule 11), read from the verdict account's own desk records, never kept
as separate state: an entry the daily run handed over (`entry_pending`) until its entry outcome is recorded, and an
open position whose exit is ordered until it is closed. Entries are rebuilt from the committed decision run that the
run log recorded, through the daily run's own decision source and order builder, so there is no second order format.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ...constants import OUTCOME_ENTRY_PENDING, RUN_LOG_DECISIONS_STEP
from ..daily_ports import DecisionSource, OrderBuilder
from ..entries import EntryOrder
from ..records import DeskRecords
from ..run_log import RunLog
from ..status import ENTRY_OUTCOMES, OpenPosition, open_positions

NOT_RECORDED = "the run log of {day} records no decision run for {book}"
NOT_IN_RUN = "the decision run {run_id} of {day} no longer gives trade {trade_id}"


class OrderMissing(LookupError):
    """A handed-over entry whose order cannot be rebuilt: the step fails, never guesses (entries fail closed)."""


@dataclass(frozen=True)
class PendingEntry:
    book: str
    trade_id: str
    day: date  # the decision day: its card carries the trade


def pending_entries(book: str, records: DeskRecords) -> list[PendingEntry]:
    events = records.event_rows()
    done = {e["trade_id"] for e in events if e["outcome"] in ENTRY_OUTCOMES}
    waiting = [e for e in events if e["outcome"] == OUTCOME_ENTRY_PENDING and e["trade_id"] not in done]
    return [PendingEntry(book, e["trade_id"], date.fromisoformat(e["day"])) for e in waiting]


def pending_exits(records: DeskRecords) -> list[OpenPosition]:
    return [p for p in open_positions(records) if p.exit_reason]


class OrderSource(ABC):
    @abstractmethod
    def order(self, pending: PendingEntry) -> EntryOrder:
        """The handed-over entry's order, as its committed decision run gives it; `OrderMissing` when it cannot."""


class RunLogOrders(OrderSource):
    def __init__(self, root: Path, decisions: DecisionSource, orders: OrderBuilder):
        self.root, self.decisions, self.orders = Path(root), decisions, orders

    def order(self, pending: PendingEntry) -> EntryOrder:
        log = RunLog.open(self.root, pending.day)
        collected = log.result(RUN_LOG_DECISIONS_STEP) if log.done(RUN_LOG_DECISIONS_STEP) else {}
        entry = collected.get(pending.book, {})
        if "run_id" not in entry:
            raise OrderMissing(NOT_RECORDED.format(day=pending.day, book=pending.book))
        decision = self.decisions.recorded(pending.book, pending.day, entry["run_id"], entry["commit"])
        for order in self.orders.orders(pending.book, decision.run, decision.committed_at):
            if order.proposal.trade_id == pending.trade_id:
                return order
        raise OrderMissing(NOT_IN_RUN.format(run_id=entry["run_id"], day=pending.day, trade_id=pending.trade_id))
