"""Entry fills (story E4, design 8): a decided trade opens at the execution snapshot, protection first.

Before any leg: the trade needs the risk manager's approval (C2) for this book, trade and day; a decision committed
before the execution snapshot started; a complete snapshot; and no open position of the book whose protection is
unverified or whose leg expired before its exit. Then the protective (bought) legs fill first, then the short legs,
each at the touch of a valid quote whose size covers the units. The first leg that does not fill stops the entry:
every leg already filled is unwound at the same snapshot (short legs bought back first, protection sold last), the
legging cost is recorded and the trade does not open. An unwind leg without a valid quote stays open as an exit
order, retried at the next snapshot.

Entry limit (orchestrator, 14 Oct 2026; judge 68): C2 checked the maximum loss on the entry it modelled (decision mids,
B2's pad, entry charges) and records that entry cash in its decision, with the proposal it judged; the limit is read
from there only, never passed in, and a decision on any other proposal is refused. When every leg is quoted, the net
entry at the touch (premium at ask/bid minus C1's charges) must be no worse than that approved entry, as a limit order
would enforce; otherwise nothing fills and the shortfall is recorded. The limit scales with the lots (legs never
fill in part). Exits are never limited.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime

from ..constants import (
    ENTRY_WORSE_THAN_APPROVED,
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
from .status import ENTRY_OUTCOMES, blocking_trades

UNWIND_PENDING = "unwind of a partial fill could not finish: {legs}"
LIMIT_TOLERANCE_RS = 1e-6  # float rounding between C2's sum and this one; far below a paisa
WORSE_THAN_APPROVED = (
    ENTRY_WORSE_THAN_APPROVED
    + ": net entry Rs {actual:,.2f} at the touch is worse than the approved Rs {approved:,.2f}"
    " by Rs {shortfall:,.2f}"
)


@dataclass(frozen=True)
class EntryOrder:
    book: str
    decision_id: str
    decided_at: datetime  # when the decision was committed (time zone aware)
    proposal: Proposal  # C2's proposal: trade ID, terms, lot size, legs
    expiry: date
    risk: RiskDecision  # C2's decision on this proposal for this book; its entry cash is the entry limit

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
    shortfall_rs: float | None = None


def entry_shortfall(order: EntryOrder, maker: FillMaker, quotes: list[LegQuote]) -> float:
    """Rupees by which the net entry at these quotes falls short of the approved entry (0 when no worse)."""
    actual = sum(maker.fill(q, FILL_OPEN).amount for q in quotes)
    shortfall = order.risk.entry_cash_rs - actual
    return shortfall if shortfall > LIMIT_TOLERANCE_RS else 0.0


def refusal(order: EntryOrder, snapshot: ExecutionSnapshot, blocked: list[str]) -> str:
    """Why the trade may not open at this snapshot, or empty when it may."""
    risk, trade_id = order.risk, order.proposal.trade_id
    if (risk.book, risk.trade_id, risk.day) != (order.book, trade_id, snapshot.day.isoformat()):
        return f"risk decision is for {risk.book} {risk.trade_id} on {risk.day}, not this trade today"
    if not risk.ok:
        return "risk manager refused: " + "; ".join(risk.reasons)
    if risk.proposal != order.proposal or risk.entry_cash_rs is None:
        return "risk decision does not carry this exact proposal and its approved entry cash"
    if order.decided_at >= snapshot.started_at:
        return f"decision committed at {order.decided_at}, not before the execution snapshot {snapshot.snapshot_id}"
    if not snapshot.complete:
        return f"execution snapshot {snapshot.snapshot_id} is incomplete: no new risk"
    if blocked:
        return f"open trade {'; '.join(blocked)} blocks new risk in {order.book}"
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
        reason = refusal(order, snapshot, blocking_trades(journal.records))
        if reason:
            return self._event(journal, order, snapshot, OUTCOME_NOT_OPENED, reason)
        maker = FillMaker(order.book, order.decision_id, trade_id, snapshot, self.charges)
        quotes = [price_leg(snapshot, leg, leg.side(opening=True), order.proposal.units) for leg in order.legs()]
        if all(q.fills for q in quotes) and (shortfall := entry_shortfall(order, maker, quotes)):
            approved = order.risk.entry_cash_rs
            reason = WORSE_THAN_APPROVED.format(actual=approved - shortfall, approved=approved, shortfall=shortfall)
            return self._event(journal, order, snapshot, OUTCOME_NOT_OPENED, reason, shortfall=shortfall)
        opened: list[LegQuote] = []
        for quote in quotes:
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
    def _event(journal, order: EntryOrder, snapshot, outcome: str, reason: str, cost=None, shortfall=None):
        trade_id = order.proposal.trade_id
        event = DeskEvent(
            f"{trade_id}:{outcome}", snapshot.day, order.book, trade_id, order.decision_id, snapshot.snapshot_id,
            snapshot.sha256, outcome, reason, cost, shortfall,
        )  # fmt: skip
        journal.record_event(event)
        return EntryResult(trade_id, outcome, reason, cost, shortfall)


def _result(row: dict[str, str]) -> EntryResult:
    cost, shortfall = (float(row[k]) if row[k] else None for k in ("legging_cost_rs", "shortfall_rs"))
    return EntryResult(row["trade_id"], row["outcome"], row["reason"], cost, shortfall)
