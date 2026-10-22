"""The ticket book (story MS-P1f): opens, closes and settles tickets with the same fill port as trades, and records
them only in the ticket ledger: an `AccountPort` the composition root keeps apart from every driver's account."""

from dataclasses import dataclass
from datetime import date, datetime

from ...constants import SIDE_SELL
from ..constants import ExitReason, Outcome
from ..contracts.accounts import AccountPort, FillPort, FillResult, LedgerEntry, SealedDecision
from ..contracts.decisions import OpenPosition
from ..contracts.seal import Seal
from ..contracts.snapshot import SlotSnapshot


def fill_cash(fill: FillResult) -> float:
    """Rupees a fill moves: premium received minus premium paid, less every charge."""
    return sum((leg.price if leg.side == SIDE_SELL else -leg.price) * leg.units - leg.charges for leg in fill.legs)


def ticket_id(sealed: SealedDecision) -> str:
    decision = sealed.decision
    return f"ticket:{decision.driver_id}:{decision.road}:{decision.session}"


def _position(sealed: SealedDecision, fill: FillResult) -> OpenPosition:
    decision, proposal = sealed.decision, sealed.decision.proposal
    return OpenPosition(ticket_id(sealed), decision.driver_id, decision.road, proposal.structure, proposal.legs,
                        proposal.lot, decision.session, fill_cash(fill), proposal.max_loss)  # fmt: skip


@dataclass(frozen=True)
class TicketBook:
    fills: FillPort
    ledger: AccountPort  # the ticket ledger; never a driver's account

    def enter(self, sealed: SealedDecision, snapshot: SlotSnapshot, seal: Seal, at: datetime) -> FillResult:
        decision = sealed.decision
        if decision.outcome != Outcome.TICKET:
            raise ValueError("the ticket book enters tickets only")
        fill = self.fills.enter(sealed, snapshot, seal, at)
        if fill.filled:
            self.ledger.record(decision.driver_id, LedgerEntry(_position(sealed, fill), fill, closes=False))
        return fill

    def exit(self, position: OpenPosition, reason: ExitReason, snapshot: SlotSnapshot, file_sha256: str, seal: Seal,
             at: datetime) -> FillResult:  # fmt: skip
        return self._close(position, self.fills.exit(position, snapshot, file_sha256, seal, at), reason)

    def settle(self, position: OpenPosition, expiry: date) -> FillResult:
        return self._close(position, self.fills.settle(position, expiry), ExitReason.EXPIRY)

    def _close(self, position: OpenPosition, fill: FillResult, reason: ExitReason) -> FillResult:
        if fill.filled:
            self.ledger.record(position.driver_id, LedgerEntry(position, fill, closes=True, exit_reason=reason))
        return fill
