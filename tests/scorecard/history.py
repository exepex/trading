"""Simulated paper histories for the scorecard tests (story E6): trades written through the real E1 account writer and
E4 desk records (fills and entry and exit events), one strategy tag per trade. The touch each fill was priced against
is kept in `SNAPSHOTS` (a fake execution snapshot source, story E2b: the fill rows no longer carry it)."""

from __future__ import annotations

from datetime import date, datetime, time

from fno.accounting.ledgers import Order
from fno.books.fills import Fill
from fno.config import ROOT, load_config
from fno.constants import FILL_CLOSE, FILL_OPEN, OUTCOME_CLOSED, OUTCOME_OPENED, SIDE_BUY, SIDE_SELL
from fno.desk.pricing import DeskLeg
from fno.desk.records import DeskEvent, FillRecord
from fno.desk.snapshot import ExecutionQuote, ExecutionSnapshot, ExecutionSnapshotSource, SnapshotError
from fno.desk.wiring import open_desk_journal
from fno.models import IST
from fno.research_engine.structures import BOUGHT, SOLD, Leg

CHARGES = load_config(ROOT / "config.yaml")["charges"]
EXPIRY = date(2027, 6, 24)
UNITS = 65
LONG = DeskLeg("NIFTY27JUN25200CE", EXPIRY, Leg(25200, "CE", BOUGHT))
SHORT = DeskLeg("NIFTY27JUN25000CE", EXPIRY, Leg(25000, "CE", SOLD))


class TouchSnapshots(ExecutionSnapshotSource):
    """The execution snapshots of a simulated history: each fill's touch, `half` either side of its mid."""

    def __init__(self):
        self.quotes: dict[tuple[date, str], dict] = {}

    def add(self, day: date, snapshot_id: str, leg: DeskLeg, bid: float, ask: float) -> None:
        key = (leg.expiry, float(leg.leg.strike), leg.leg.kind)
        quote = ExecutionQuote("", leg.expiry, float(leg.leg.strike), leg.leg.kind, bid, ask, 1e6, 1e6, True, "", True)
        self.quotes.setdefault((day, snapshot_id), {})[key] = quote

    def snapshot(self, day: date, snapshot_id: str) -> ExecutionSnapshot:
        if (day, snapshot_id) not in self.quotes:
            raise SnapshotError(f"snapshot {snapshot_id} of {day} is not in the quote store")
        moment = datetime.combine(day, time(15, 15), IST)
        return ExecutionSnapshot(day, snapshot_id, SNAPSHOT_SHA, SNAPSHOT_SHA, moment, moment, True,
                                 self.quotes[(day, snapshot_id)])  # fmt: skip


SNAPSHOT_SHA = "0" * 64
SNAPSHOTS: dict[str, TouchSnapshots] = {}  # per test root (its path), filled by `trade`


def snapshots_of(root) -> TouchSnapshots:
    return SNAPSHOTS.setdefault(str(root), TouchSnapshots())


def _record(root, book, strategy, trade_id, action, leg, side, price, half, day) -> FillRecord:
    when = datetime.combine(day, time(15, 15, 40), IST)
    order = Order(side, price, UNITS, 0.0)
    fill = Fill.priced(f"{trade_id}:{action}:{leg.contract}", trade_id, when, leg.contract, order, CHARGES)
    mid = price - half if side == SIDE_BUY else price + half
    snapshot = f"snap-{day.isoformat()}-{trade_id}"  # one snapshot per simulated trade: each has its own touches
    snapshots_of(root).add(day, snapshot, leg, mid - half, mid + half)
    return FillRecord(book, strategy, f"d-{trade_id}", action, snapshot, SNAPSHOT_SHA, leg, "", True, fill)


def _event(book, strategy, trade_id, outcome, day, reason="", **amounts) -> DeskEvent:
    return DeskEvent(f"{trade_id}:{outcome}", day, book, strategy, trade_id, f"d-{trade_id}", f"snap-{day}", "0" * 64,
                     outcome, reason, **amounts)  # fmt: skip


def trade(root, book, strategy, trade_id, opened, closed=None, credit=50.0, debit=None, half=0.5):
    """A one-lot call spread: sell 25000 CE at `credit` + 20, buy 25200 CE at 20 (net credit `credit` a unit); closed
    at net `debit` a unit (25000 CE bought back at debit + 10, 25200 CE sold at 10). Each fill at the touch `half` away
    from its mid. Open when `closed` is None."""
    with open_desk_journal(book, root) as journal:
        journal.record_fill(_record(root, book, strategy, trade_id, FILL_OPEN, LONG, SIDE_BUY, 20.0, half, opened))
        credit_fill = _record(root, book, strategy, trade_id, FILL_OPEN, SHORT, SIDE_SELL, credit + 20.0, half, opened)
        journal.record_fill(credit_fill)
        journal.record_event(_event(book, strategy, trade_id, OUTCOME_OPENED, opened))
        if closed is not None:
            buy_back = _record(root, book, strategy, trade_id, FILL_CLOSE, SHORT, SIDE_BUY, debit + 10.0, half, closed)
            journal.record_fill(buy_back)
            journal.record_fill(
                _record(root, book, strategy, trade_id, FILL_CLOSE, LONG, SIDE_SELL, 10.0, half, closed)
            )
            journal.record_event(_event(book, strategy, trade_id, OUTCOME_CLOSED, closed))


def event(root, book, strategy, trade_id, outcome, day, reason="", **amounts):
    with open_desk_journal(book, root) as journal:
        journal.record_event(_event(book, strategy, trade_id, outcome, day, reason, **amounts))
