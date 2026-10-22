"""After the seal (story MS-P1j; order: seal, fills, exits): every sealed trade fills at its road's touch, every ticket
through the ticket book; then the exits the cards called. Per road, MS-P1f's `allocate` serves the slot's fills against
the displayed size, accounts first in a seeded order; only servable account entries are recorded, each other one is
`unavailable: size_shared` and stays in every denominator. Exits are recorded as filled (each account is measured on
its own); an unservable exit leaves its outcome out of the rupee sum (`unservable`). Outcomes are rebuilt from the
ledgers afterwards (`outcomes.outcomes_of`). NIFTY fills get their 15:15
drift rows, never a fill."""

from dataclasses import dataclass
from datetime import datetime

from ...desk.snapshot import ExecutionSnapshot
from ..constants import SLOT_1500, Outcome
from ..contracts.accounts import FillResult, LedgerEntry, SealedDecision
from ..contracts.records import DecisionRecord, DriftRow, ExitRecord
from ..contracts.seal import Seal
from ..execution.drift import drift_rows
from ..tickets.shared_size import OwnedFill, allocate
from .books import Books, EntryMids
from .ledgers import open_positions
from .outcomes import TICKET_PREFIX
from .running_view import opened_position, position_id
from .slot import SlotRoads


@dataclass(frozen=True)
class SlotFills:
    entries: dict[tuple, FillResult]  # (road, driver id) -> the entry fill of its sealed trade or ticket
    size_shared: frozenset[tuple]  # (road, driver id) of the account entries the displayed size could not serve
    unservable: frozenset[tuple[str, FillResult]]  # for `account_net`
    drift: tuple[DriftRow, ...]

    @property
    def fills(self) -> tuple[FillResult, ...]:
        return tuple(self.entries.values())


@dataclass(frozen=True)
class FillStep:
    books: Books
    capture_1515: ExecutionSnapshot | None
    entry_mids: EntryMids

    def run(self, roads: SlotRoads, records: tuple[DecisionRecord, ...], exits: tuple[ExitRecord, ...], seal: Seal,
            at: datetime) -> SlotFills:  # fmt: skip
        snapshots = roads.marks
        entered = [(r, self._enter(r, snapshots[r.road], seal, at)) for r in records
                   if r.decision.outcome in (Outcome.TRADE, Outcome.TICKET)]  # fmt: skip
        closings = [self._exit(e, snapshots[e.road], seal, at) for e in exits]
        owned: dict = {}
        for record, fill in entered:
            is_ticket = record.decision.outcome == Outcome.TICKET
            owned.setdefault(record.road, []).append(OwnedFill(record.decision.driver_id, fill, is_ticket))
        for closing, is_ticket in closings:
            if closing is not None:
                owned.setdefault(closing.position.road, []).append(
                    OwnedFill(closing.position.driver_id, closing.fill, is_ticket))  # fmt: skip
        allocations = [allocate(fills, snapshots[road], SLOT_1500) for road, fills in owned.items()]
        unservable = frozenset().union(*(a.unservable_fills for a in allocations))
        accounts = [(r, f) for r, f in entered if r.decision.outcome == Outcome.TRADE]
        shared = frozenset(_key(r) for r, f in accounts if (r.decision.driver_id, f) in unservable)
        served = [(r, f) for r, f in accounts if f.filled and _key(r) not in shared]
        for record, fill in served:
            self.books.accounts.record(
                record.decision.driver_id, LedgerEntry(opened_position(record.decision, fill.cash), fill, closes=False)
            )
        session = roads.scheduled[0].session
        drift = tuple(row for r, f in served for row in self._drift(session, r, f))
        return SlotFills({_key(r): f for r, f in entered}, shared, unservable, drift)

    def _drift(self, session, record: DecisionRecord, fill: FillResult) -> tuple[DriftRow, ...]:
        return drift_rows(session, position_id(record.decision), record.road, fill, self.capture_1515)

    def _enter(self, record: DecisionRecord, snapshot, seal: Seal, at: datetime) -> FillResult:
        if record.decision.outcome == Outcome.TICKET:
            return self.books.tickets.enter(record, seal.sha256, snapshot, seal, at)
        return self.books.fills.enter(SealedDecision(record.decision, seal.sha256), snapshot, seal, at)

    def _exit(self, exit_: ExitRecord, snapshot, seal: Seal, at: datetime):
        """(closing entry or None, is_ticket): the ticket book records its own closes; an account's is recorded here."""
        is_ticket = exit_.position_id.startswith(TICKET_PREFIX)
        reader = self.books.ticket_entries if is_ticket else self.books.account_entries
        position = next(p for p in open_positions(reader.entries(exit_.driver_id))
                        if p.position_id == exit_.position_id)  # fmt: skip
        if is_ticket:
            fill = self.books.tickets.exit(position, exit_.exit_reason, snapshot, seal.sha256, seal, at)
        else:
            fill = self.books.fills.exit(position, snapshot, seal.sha256, seal, at)
        if not fill.filled:
            return None, is_ticket
        closing = LedgerEntry(position, fill, closes=True, exit_reason=exit_.exit_reason)
        if not is_ticket:
            self.books.accounts.record(position.driver_id, closing)
        return closing, is_ticket


def _key(record: DecisionRecord) -> tuple:
    return record.road, record.decision.driver_id
