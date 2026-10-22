"""The expiries a road must record, from NSE's stored F&O files by the recorder's own rules (A5's point-in-time
monthlies for A4 and A4c, the nearest weeklies for A4f). The capture's sidecar is compared with this, never trusted."""

from datetime import date

from ...quotes.expiry_listing import ExpiryListUnavailable, ListedExpiries
from ...quotes.monthly_contracts import PointInTimeMonthlies
from ...quotes.recorder import MONTHLY_EXPIRIES
from ...quotes.weekly import WEEKLY_EXPIRIES, nearest_weeklies
from ..constants import ExpiryKind
from ..contracts.roads import Road
from .ports import ExpiryUnavailable


class ListedRoadExpiries:
    def __init__(self, listed: ListedExpiries, monthlies: PointInTimeMonthlies):
        self.listed, self.monthlies = listed, monthlies

    def expected(self, road: Road, session: date) -> tuple[date, ...]:
        try:
            listed, _ = self.listed.listed(road.underlying, session)  # the previous session's NSE file
            monthly, _ = self.monthlies.monthlies(road.underlying, listed, session)
        except (ExpiryListUnavailable, ValueError, KeyError) as error:  # a store outage is not caught: it propagates
            raise ExpiryUnavailable(f"{road.underlying} {session}: {error}") from error
        months = sorted(monthly)[:MONTHLY_EXPIRIES]
        if road.expiry_kind is ExpiryKind.MONTHLY:
            return tuple(months)
        return tuple(nearest_weeklies(listed, months, session, WEEKLY_EXPIRIES))
