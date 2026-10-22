"""Accounts and fills (stories 3.3, 3.6): one paper account per driver version; fills at the decision snapshot's
touch after the seal, never partial and never invented."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol, runtime_checkable

from ...constants import SIDES
from ..constants import ExitState, RefusalReason
from .dashcam import Seal
from .decisions import Decision, OpenPosition
from .safety import AccountView
from .snapshot import ContractKey, SlotSnapshot


@dataclass(frozen=True)
class FilledLeg:
    key: ContractKey
    side: str
    units: int
    price: float  # the touch: ask to buy, bid to sell
    charges: float  # C1's charges on this fill

    def __post_init__(self):
        if self.side not in SIDES or self.units < 1 or self.price < 0 or self.charges < 0:
            raise ValueError("a filled leg needs a side, units, and no negative price or charge")


@dataclass(frozen=True)
class FillResult:
    """Every leg filled, or none with the reasons; a position that could not close names its state."""

    legs: tuple[FilledLeg, ...] = ()
    refused: tuple[RefusalReason, ...] = ()
    state: ExitState | None = None
    filled_at: datetime | None = None
    seal_sha256: str = ""  # the decision file this fill rests on

    def __post_init__(self):
        if bool(self.legs) == bool(self.refused or self.state):
            raise ValueError("a fill result is either filled legs or a refusal or state, never both or neither")
        if self.legs and (self.filled_at is None or not self.seal_sha256):
            raise ValueError("filled legs carry their time and the seal they rest on")

    @property
    def filled(self) -> bool:
        return bool(self.legs)


@runtime_checkable
class AccountPort(Protocol):
    def view(self, driver_id: str, snapshot: SlotSnapshot) -> AccountView:
        """The driver's account at this slot, opened at the school's `account_rs` on first use."""

    def record(self, driver_id: str, result: FillResult) -> None:
        """Append a filled result to the driver's ledger; a refusal or state records nothing."""


@runtime_checkable
class FillPort(Protocol):
    def enter(self, decision: Decision, snapshot: SlotSnapshot, seal: Seal) -> FillResult: ...

    def exit(self, position: OpenPosition, snapshot: SlotSnapshot, reason: str, seal: Seal) -> FillResult: ...

    def settle(self, position: OpenPosition, expiry: date) -> FillResult: ...
