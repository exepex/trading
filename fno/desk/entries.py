"""Entry fills (story E4, design 8): a decided trade opens at the execution snapshot, protection first.

Before any leg: the trade needs the risk manager's approval (C2) for this book, trade and day; a decision committed
before the execution snapshot started; a complete snapshot; and no open position of the book whose protection is
unverified. Then the protective (bought) legs fill first, then the short legs, each at the touch of a valid quote whose
size covers the units. The first leg that does not fill stops the entry: every leg already filled is unwound at the
same snapshot (short legs bought back first, protection sold last), the legging cost is recorded and the trade does
not open. An unwind leg without a valid quote stays open as an exit order, retried at the next snapshot.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime

from ..constants import (
    FILL_OPEN,
    FILL_UNWIND,
    OUTCOME_EXIT_ORDERED,
    OUTCOME_NOT_OPENED,
    OUTCOME_OPENED,
    OUTCOME_PARTIAL_FILL,
)
from ..models import now_ist
from ..risk.inputs import Proposal
from ..risk.manager import RiskDecision
from .execution import FillMaker, check_point_in_time, closing_quotes, legging_cost
from .pricing import DeskLeg, LegQuote, price_leg
from .records import DeskEvent, DeskJournal
from .snapshot import ExecutionSnapshot
from .status import ENTRY_OUTCOMES, unverified_trades

UNWIND_PENDING = "unwind of a partial fill could not finish: {legs}"


@dataclass(frozen=True)
class EntryOrder:
    book: str
    decision_id: str
    decided_at: datetime  # when the decision was committed (time zone aware)
    proposal: Proposal  # C2's proposal: trade ID, terms, lot size, legs
    expiry: date
    risk: RiskDecision  # C2's decision on this proposal for this book

    def legs(self) -> list[DeskLeg]:
        """Protective legs first, then short legs (design 8), each in the decision's order."""
        legs = [DeskLeg(p.contract, self.expiry, p.leg) for p in self.proposal.legs]
        return [leg for leg in legs if leg.protective] + [leg for leg in legs if not leg.protective]


@dataclass(frozen=True)
class EntryResult:
    trade_id: str
    outcome: str
    reason: str
    legging_cost_rs: float | None = None


def refusal(order: EntryOrder, snapshot: ExecutionSnapshot, blocked: list[str]) -> str:
    """Why the trade may not open at this snapshot, or empty when it may."""
    risk, trade_id = order.risk, order.proposal.trade_id
    if (risk.book, risk.trade_id, risk.day) != (order.book, trade_id, snapshot.day.isoformat()):
        return f"risk decision is for {risk.book} {risk.trade_id} on {risk.day}, not this trade today"
    if not risk.ok:
        return "risk manager refused: " + "; ".join(risk.reasons)
    if order.decided_at >= snapshot.started_at:
        return f"decision committed at {order.decided_at}, not before the execution snapshot {snapshot.snapshot_id}"
    if not snapshot.complete:
        return f"execution snapshot {snapshot.snapshot_id} is incomplete: no new risk"
    if blocked:
        return f"protection unverified on open trade {', '.join(blocked)}: no new risk in {order.book}"
    return ""


class EntryDesk:
    def __init__(self, charges: Mapping[str, float], clock=now_ist):
        self.charges, self.clock = dict(charges), clock

    def enter(self, order: EntryOrder, snapshot: ExecutionSnapshot, journal: DeskJournal) -> EntryResult:
        """Open the trade or record why not. A rerun repeats nothing: it returns the recorded outcome."""
        check_point_in_time(snapshot, self.clock())
        trade_id = order.proposal.trade_id
        done = [r for r in journal.records.event_rows(trade_id) if r["outcome"] in ENTRY_OUTCOMES]
        if done:
            return _result(done[0])
        reason = refusal(order, snapshot, unverified_trades(journal.records))
        if reason:
            return self._event(journal, order, snapshot, OUTCOME_NOT_OPENED, reason)
        maker = FillMaker(order.book, order.decision_id, trade_id, snapshot, self.charges)
        opened: list[LegQuote] = []
        for leg in order.legs():
            quote = price_leg(snapshot, leg, leg.side(opening=True), order.proposal.units)
            if not quote.fills:
                return self._unwind(journal, order, snapshot, maker, opened, quote)
            journal.record_fill(maker.record(quote, FILL_OPEN))
            opened.append(quote)
        return self._event(journal, order, snapshot, OUTCOME_OPENED, f"{len(opened)} legs filled")

    def _unwind(self, journal, order, snapshot, maker: FillMaker, opened: list[LegQuote], failed: LegQuote):
        reason = f"{failed.leg.contract} did not fill: {failed.reason}"
        if not opened:
            return self._event(journal, order, snapshot, OUTCOME_NOT_OPENED, reason)
        closing, pending = closing_quotes(snapshot, [(q.leg, q.units) for q in opened])
        for quote in closing:
            journal.record_fill(maker.record(quote, FILL_UNWIND))
        if pending:  # the legging cost is known only once the last leg is unwound (the exit's close records it)
            legs = "; ".join(f"{q.leg.contract} ({q.reason})" for q in pending)
            result = self._event(journal, order, snapshot, OUTCOME_PARTIAL_FILL, reason)
            self._event(journal, order, snapshot, OUTCOME_EXIT_ORDERED, UNWIND_PENDING.format(legs=legs))
            return result
        fills = [maker.fill(q, FILL_OPEN) for q in opened] + [maker.fill(q, FILL_UNWIND) for q in closing]
        return self._event(journal, order, snapshot, OUTCOME_PARTIAL_FILL, reason, legging_cost(fills))

    @staticmethod
    def _event(journal, order: EntryOrder, snapshot, outcome: str, reason: str, cost: float | None = None):
        trade_id = order.proposal.trade_id
        event = DeskEvent(
            f"{trade_id}:{outcome}", snapshot.day, order.book, trade_id, order.decision_id, snapshot.snapshot_id,
            snapshot.sha256, outcome, reason, cost,
        )  # fmt: skip
        journal.record_event(event)
        return EntryResult(trade_id, outcome, reason, cost)


def _result(row: dict[str, str]) -> EntryResult:
    cost = float(row["legging_cost_rs"]) if row["legging_cost_rs"] else None
    return EntryResult(row["trade_id"], row["outcome"], row["reason"], cost)
