"""Roads (story 3.1): where a decision can happen. Five fixed roads, each one capture dataset at the 15:00 slot."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol, runtime_checkable

from ..constants import ClosureReason, ExpiryKind, RoadCode


@dataclass(frozen=True)
class Road:
    code: RoadCode
    underlying: str
    expiry_kind: ExpiryKind
    dataset: str  # the quote store's dataset folder
    stem: str  # the capture file stem (`<stem>_<YYYYMMDD>.canonical`)


ROADS = (
    Road(RoadCode.NIFTY_MONTHLY, "NIFTY", ExpiryKind.MONTHLY, "quote-snapshots", "nifty"),
    Road(RoadCode.BANKNIFTY_MONTHLY, "BANKNIFTY", ExpiryKind.MONTHLY, "quote-snapshots", "banknifty"),
    Road(RoadCode.FINNIFTY_MONTHLY, "FINNIFTY", ExpiryKind.MONTHLY, "quote-snapshots", "finnifty"),
    Road(RoadCode.MIDCPNIFTY_MONTHLY, "MIDCPNIFTY", ExpiryKind.MONTHLY, "quote-snapshots", "midcpnifty"),
    Road(RoadCode.NIFTY_WEEKLY, "NIFTY", ExpiryKind.WEEKLY, "quote-snapshots-weekly", "niftyweekly"),
)
ROADS_BY_CODE = {road.code: road for road in ROADS}


@dataclass(frozen=True)
class DatedLot:
    units: int  # contract multiplier in force that session
    source: str  # where it was read (e.g. the A20a master file's path), so a mismatch can be named


@dataclass(frozen=True)
class RoadStatus:
    """Open, or closed with exactly one reason."""

    closed_by: ClosureReason | None = None

    @property
    def open(self) -> bool:
        return self.closed_by is None


OPEN = RoadStatus()


@dataclass(frozen=True)
class RoadDay:
    road: Road
    session: date
    expiries: tuple[date, ...]  # the expiries the road's capture records that session, nearest first
    lot: DatedLot | None
    strike_step: float | None
    status: RoadStatus

    def __post_init__(self):
        if self.status.open and (self.lot is None or self.strike_step is None or not self.expiries):
            raise ValueError("an open road needs its expiries, dated lot and strike step")
        if tuple(sorted(self.expiries)) != self.expiries:
            raise ValueError("expiries must be nearest first")


@runtime_checkable
class RoadCatalogue(Protocol):
    def day(self, session: date) -> tuple[RoadDay, ...]:
        """Every road of a trading session (closed ones with their reason); none on a non-trading day."""
