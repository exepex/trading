"""The exit review at each scheduled execution snapshot (story E4, design 8 and 9), for every open position of a book:

1. A leg that expired before its exit filled is cash-settled at its intrinsic value against NSE's final settlement
   price (story E7), with C1's settlement charges. Until the expiry day's file is published the position is
   `settlement_needed` (alert): it blocks the book's new risk and is never priced from a last or stale price.
2. A protective leg without a valid quote marks the position `protection_unverified` (the book opens no new risk while
   it is open) and orders its exit.
3. An exit already ordered, or an exit rule reached now, closes the position at this snapshot's valid quotes: short
   legs bought back first, protection sold last. A leg without a valid quote is a pending exit with an alert, retried
   at the next scheduled snapshot. The position is closed only when every exit fill is recorded.

Price rules are not judged at the snapshot that opened the position (its value there is only the spread just paid).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ..alerts.sender import AlertSender
from ..books.equity import trade_positions
from ..constants import (
    FILL_CLOSE,
    NIFTY_SYMBOL,
    OUTCOME_CLOSED,
    OUTCOME_EXIT_ORDERED,
    OUTCOME_PARTIAL_FILL,
    OUTCOME_PENDING_EXIT,
    OUTCOME_PROTECTION_UNVERIFIED,
    OUTCOME_SETTLEMENT_NEEDED,
)
from ..models import now_ist
from .execution import FillMaker, check_point_in_time, closing_quotes
from .exit_rules import ExitContext, ExitRule
from .pricing import price_leg
from .records import DeskEvent, DeskJournal
from .settlement import SettlementError, SettlementPrices, settlement_record
from .snapshot import ExecutionSnapshot
from .status import OpenPosition, open_positions

HELD = "held"
NO_RULES = "no exit rules given for this open trade"
ALERT = "F&O paper desk {book}: trade {trade_id} {outcome}: {reason}"


def exit_decision_id(trade_id: str) -> str:
    """The decision ID an exit's fills and events carry: the trade's exit order."""
    return f"{trade_id}:{OUTCOME_EXIT_ORDERED}"


@dataclass(frozen=True)
class ExitResult:
    trade_id: str
    outcome: str
    reason: str
    alerts: tuple[str, ...] = ()  # each alert's send outcome


class ExitDesk:
    def __init__(self, charges: Mapping[str, float], alerts: AlertSender, settlements: SettlementPrices, clock=now_ist):
        self.charges, self.alerts, self.settlements, self.clock = dict(charges), alerts, settlements, clock

    def review(
        self, book: str, snapshot: ExecutionSnapshot, journal: DeskJournal, rules: Mapping[str, Sequence[ExitRule]]
    ) -> list[ExitResult]:
        check_point_in_time(snapshot, self.clock())
        positions = open_positions(journal.records)
        return [self._review(book, p, snapshot, journal, rules.get(p.trade_id)) for p in positions]

    def _review(self, book, position: OpenPosition, snapshot, journal, rules) -> ExitResult:
        check_point_in_time(snapshot, self.clock(), not_before=position.last_fill_at)
        maker = FillMaker(book, exit_decision_id(position.trade_id), position.trade_id, snapshot, self.charges)
        if any(leg.expiry < snapshot.day for leg, _ in position.holdings):
            return self._settle(book, position, snapshot, journal)
        unquotable = [
            leg.contract for leg, units in position.holdings
            if leg.protective and not price_leg(snapshot, leg, leg.side(opening=False), units).fills
        ]  # fmt: skip
        alerts, reason = (), ""
        if unquotable:
            reason = f"{OUTCOME_PROTECTION_UNVERIFIED}: no valid quote for protective leg {', '.join(unquotable)}"
            marked = self._event(book, position, snapshot, journal, OUTCOME_PROTECTION_UNVERIFIED, reason,
                                 snapshot.snapshot_id)  # fmt: skip
            alerts = marked.alerts
        reason = position.exit_reason or reason
        if not reason and position.opened_by != snapshot.snapshot_id:
            if rules is None:
                return self._alert(book, position.trade_id, HELD, NO_RULES)
            context = ExitContext(snapshot.day, self._net_if_closed(position, snapshot, maker))
            reason = next((r for r in (rule.reached(position, context) for rule in rules) if r), "")
        if not reason:
            return ExitResult(position.trade_id, HELD, "no exit rule reached")
        if not position.exit_reason:
            self._event(book, position, snapshot, journal, OUTCOME_EXIT_ORDERED, reason)
        result = self._close(book, position, snapshot, journal, maker)
        return ExitResult(result.trade_id, result.outcome, result.reason, alerts + result.alerts)

    def _close(self, book, position: OpenPosition, snapshot, journal: DeskJournal, maker: FillMaker) -> ExitResult:
        closing, pending = closing_quotes(snapshot, position.holdings)
        for quote in closing:
            journal.record_fill(maker.record(quote, FILL_CLOSE))
        if pending:
            reason = "; ".join(f"{q.leg.contract}: {q.reason}" for q in pending) + " (retried at the next snapshot)"
            return self._event(book, position, snapshot, journal, OUTCOME_PENDING_EXIT, reason, snapshot.snapshot_id)
        return self._closed(book, position, snapshot, journal, "every leg closed")

    def _settle(self, book, position: OpenPosition, snapshot, journal: DeskJournal) -> ExitResult:
        """Expired legs close at NSE's final settlement (E7), one expiry at a time; a missing or unclear settlement
        price leaves the trade `settlement_needed`."""
        for expiry in sorted({leg.expiry for leg, _ in position.holdings if leg.expiry < snapshot.day}):
            try:
                final = self.settlements.final_settlement(NIFTY_SYMBOL, expiry)
                missing = f"NSE's F&O file of {expiry} (the final settlement price) is not published yet"
            except SettlementError as problem:
                final, missing = None, str(problem)
            if final is None:
                legs = ", ".join(leg.contract for leg, _ in position.holdings if leg.expiry == expiry)
                reason = f"{legs} expired on {expiry} before the exit filled: {missing}"
                return self._event(book, position, snapshot, journal, OUTCOME_SETTLEMENT_NEEDED, reason, snapshot.day)
            decision, trade_id = exit_decision_id(position.trade_id), position.trade_id
            for leg, units in (h for h in position.holdings if h[0].expiry == expiry):
                journal.record_fill(settlement_record(book, decision, trade_id, leg, units, final, self.charges))
            how = f"settled at NSE's final settlement price {final.price:,.2f} ({final.source})"
        if trade_positions(journal.records.account.fills())[position.trade_id].is_open:
            return ExitResult(position.trade_id, HELD, how + "; legs of later expiries stay open")
        return self._closed(book, position, snapshot, journal, f"every leg closed, {how}")

    def _closed(self, book, position: OpenPosition, snapshot, journal: DeskJournal, how: str) -> ExitResult:
        net = trade_positions(journal.records.account.fills())[position.trade_id].cash_flow
        partial = any(e["outcome"] == OUTCOME_PARTIAL_FILL for e in journal.records.event_rows(position.trade_id))
        reason = f"{how}; net Rs {net:,.2f}"
        return self._event(book, position, snapshot, journal, OUTCOME_CLOSED, reason, cost=-net if partial else None)

    def _net_if_closed(self, position: OpenPosition, snapshot, maker: FillMaker) -> float | None:
        quotes = [price_leg(snapshot, leg, leg.side(opening=False), units) for leg, units in position.holdings]
        if not all(q.fills for q in quotes):
            return None
        return position.cash_flow + sum(maker.fill(q, FILL_CLOSE).amount for q in quotes)

    def _event(self, book, position, snapshot, journal, outcome, reason, once_per="", cost=None) -> ExitResult:
        """Record the event once (per snapshot or day when `once_per` is given); a new pending, unverified or settlement
        event is also sent as an alert."""
        event_id = ":".join(filter(None, (position.trade_id, outcome, str(once_per))))
        event = DeskEvent(event_id, snapshot.day, book, position.trade_id, exit_decision_id(position.trade_id),
                          snapshot.snapshot_id, snapshot.sha256, outcome, reason, cost)  # fmt: skip
        new = journal.record_event(event)
        if new and outcome in (OUTCOME_PENDING_EXIT, OUTCOME_PROTECTION_UNVERIFIED, OUTCOME_SETTLEMENT_NEEDED):
            return self._alert(book, position.trade_id, outcome, reason)
        return ExitResult(position.trade_id, outcome, reason)

    def _alert(self, book: str, trade_id: str, outcome: str, reason: str) -> ExitResult:
        sent = self.alerts.send(ALERT.format(book=book, trade_id=trade_id, outcome=outcome, reason=reason))
        return ExitResult(trade_id, outcome, reason, (sent,))
