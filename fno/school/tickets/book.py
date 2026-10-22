"""The ticket book (story MS-P1f): opens, closes and settles tickets with the same fill port as trades, after the
same laws (account limits relaxed), and records them only in the ticket ledger, never in a driver's account."""

from dataclasses import dataclass
from datetime import date, datetime

from ..constants import ExitReason, Outcome
from ..contracts.accounts import AccountPort, FillPort, FillResult, LedgerEntry, SealedDecision
from ..contracts.decisions import OpenPosition
from ..contracts.safety import LawResult
from ..contracts.seal import Seal
from ..contracts.snapshot import SlotSnapshot
from .rules import first_binding_refusal


def ticket_id(sealed: SealedDecision) -> str:
    decision = sealed.decision
    return f"ticket:{decision.driver_id}:{decision.road}:{decision.session}"


def _position(sealed: SealedDecision, fill: FillResult) -> OpenPosition:
    decision, proposal = sealed.decision, sealed.decision.proposal
    return OpenPosition(ticket_id(sealed), decision.driver_id, decision.road, proposal.structure, proposal.legs,
                        proposal.lot, decision.session, fill.cash, proposal.max_loss)  # fmt: skip


@dataclass(frozen=True)
class TicketLedger:
    """Its own type, so the composition root cannot hand a driver's account to the ticket book by mistake."""

    store: AccountPort  # an account store on its own root, apart from every driver account


@dataclass(frozen=True)
class TicketBook:
    fills: FillPort
    ledger: TicketLedger

    def enter(self, sealed: SealedDecision, results: tuple[LawResult, ...], snapshot: SlotSnapshot, seal: Seal,
              at: datetime) -> FillResult:  # fmt: skip
        """`results`: the decision's sealed law results. A law that binds a ticket refuses it before any fill."""
        decision = sealed.decision
        if decision.outcome != Outcome.TICKET:
            raise ValueError("the ticket book enters tickets only")
        binding = first_binding_refusal(results)
        if binding is not None:
            return FillResult(refused=(binding,))
        fill = self.fills.enter(sealed, snapshot, seal, at)
        if fill.filled:
            self.ledger.store.record(decision.driver_id, LedgerEntry(_position(sealed, fill), fill, closes=False))
        return fill

    def exit(self, position: OpenPosition, reason: ExitReason, snapshot: SlotSnapshot, file_sha256: str, seal: Seal,
             at: datetime) -> FillResult:  # fmt: skip
        return self._close(position, self.fills.exit(position, snapshot, file_sha256, seal, at), reason)

    def settle(self, position: OpenPosition, expiry: date) -> FillResult:
        return self._close(position, self.fills.settle(position, expiry), ExitReason.EXPIRY)

    def _close(self, position: OpenPosition, fill: FillResult, reason: ExitReason) -> FillResult:
        if fill.filled:
            self.ledger.store.record(position.driver_id, LedgerEntry(position, fill, closes=True, exit_reason=reason))
        return fill
