"""Which fired decisions become tickets (story MS-P1f). The fleet (MS-P1j) calls these in this order for one driver
at one slot: `limit_trades` on the fired decisions, then the safety laws on each trade in rank order, then
`after_laws` on each result; a ticket's own laws are the same laws, read by `ticket_laws_pass`."""

from dataclasses import replace

from ..constants import Outcome, RefusalReason, TicketReason
from ..contracts.decisions import Decision
from ..contracts.roads import ROADS
from ..contracts.safety import LawResult

# Limits on the account, which a ticket does not have; every other law (protected, max loss, quote gate) binds it.
ACCOUNT_LIMITS = frozenset({RefusalReason.BUCKET_CAP, RefusalReason.OPEN_RISK, RefusalReason.NEW_RISK_DAY,
                            RefusalReason.MARGIN_ROOM, RefusalReason.DAILY_STOP, RefusalReason.BRAKE})  # fmt: skip
STOPS = frozenset({RefusalReason.DAILY_STOP, RefusalReason.BRAKE})
_ROAD_ORDER = {road.code: index for index, road in enumerate(ROADS)}


def limit_trades(fired: tuple[Decision, ...], max_new: int) -> tuple[Decision, ...]:
    """The best `max_new` by the card's frozen score stay trades (ties: the fixed road order); the rest become
    `ticket: trade_limit`. Decisions that did not fire pass through unchanged, in the given order."""
    trades = [d for d in fired if d.outcome == Outcome.TRADE]
    ranked = sorted(trades, key=lambda d: (-d.proposal.score, _ROAD_ORDER[d.road]))
    kept = {id(d) for d in ranked[:max_new]}
    return tuple(d if d.outcome != Outcome.TRADE or id(d) in kept else as_ticket(d, TicketReason.TRADE_LIMIT)
                 for d in fired)  # fmt: skip


def after_laws(decision: Decision, results: tuple[LawResult, ...]) -> Decision:
    """A trade every law passed stays a trade. One refused only by account limits, a stop among them, becomes
    `ticket: driver_stopped`. Any other refusal is `refused` with the first refusing law's reason (law order)."""
    if decision.outcome != Outcome.TRADE:
        raise ValueError("only a trade goes through the account's laws")
    refusals = [r.reason for r in results if not r.passed]
    if not refusals:
        return decision
    if set(refusals) <= ACCOUNT_LIMITS and set(refusals) & STOPS:
        return as_ticket(decision, TicketReason.DRIVER_STOPPED)
    return replace(decision, outcome=Outcome.REFUSED, reason=refusals[0])


def ticket_laws_pass(results: tuple[LawResult, ...]) -> bool:
    """A ticket's laws: every refusal must be an account limit (relaxed for tickets) for it to stand."""
    return all(r.passed or r.reason in ACCOUNT_LIMITS for r in results)


def as_ticket(decision: Decision, reason: TicketReason) -> Decision:
    if any(leg.lots != 1 for leg in decision.proposal.legs):
        raise ValueError("a ticket is one lot: the drivers size every structure at one lot (response 325 4.1)")
    return replace(decision, outcome=Outcome.TICKET, reason=reason)
