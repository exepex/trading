"""What the road catalogue asks of the outside: the dated lot and the listed expiries of a road (story 3, `roads/`)."""

from datetime import date
from typing import Protocol, runtime_checkable

from ..contracts.roads import DatedLot, Road
from ..quality.ports import ListingUnavailable


class ExpiryUnavailable(ListingUnavailable):
    """The listing that says which expiries a road records cannot be read for the session."""


@runtime_checkable
class LotSource(Protocol):
    def lot(self, underlying: str, session: date, expiries: tuple[date, ...]) -> DatedLot | None:
        """The one lot in force that session for every expiry given, or None: no file, no row for the underlying or an
        expiry month, or the expiries carry different lots."""


@runtime_checkable
class ExpirySource(Protocol):
    def expected(self, road: Road, session: date) -> tuple[date, ...]:
        """The expiries the road's capture must record that session, nearest first (A4's two monthlies, A4f's two
        weeklies), worked out from NSE's stored F&O files, never from the capture itself."""
