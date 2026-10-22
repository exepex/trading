"""The roads of a historical session (story MS-SIM-c), each open or closed with exactly one reason.

Read in the pilot's order, stopping at the first fault: the data window (DATA_SPEND), then no archived chain or index
close (`capture_missing`), then fewer than the two expiries the road records (`expiry_mismatch`), then no single dated
lot (`lot_mismatch`). A road outside the window is closed with `capture_missing` and the detail `not_in_data_spend`: the
closure reasons belong to the pilot, and the detail says what is true here."""

from collections.abc import Sequence
from datetime import date

from ....research_data.calendar import SessionCalendar
from ....storage.trading_days import is_trading_day
from ...constants import ClosureReason, ExpiryKind
from ...contracts.roads import OPEN, ROADS, DatedLot, Road, RoadDay, RoadStatus
from ..history.ports import DayChain, HistoricalChain
from ..terms import DatedTerms
from ..windows import PracticeWindows
from .steps import strike_step

EXPIRIES_RECORDED = 2  # A4 records two monthlies, A4f two weeklies


class HistoricalRoadCatalogue:
    def __init__(self, calendar: SessionCalendar, chain: HistoricalChain, terms: DatedTerms, windows: PracticeWindows,
                 roads: Sequence[Road] = ROADS):  # fmt: skip
        self.calendar, self.chain, self.terms, self.windows, self.roads = calendar, chain, terms, windows, roads

    def day(self, session: date) -> tuple[RoadDay, ...]:
        if not is_trading_day(self.calendar, session):
            return ()
        return tuple(self._road_day(road, session) for road in self.roads)

    def _road_day(self, road: Road, session: date) -> RoadDay:
        if refusal := self.windows.check(road.code, session):
            return _closed(road, session, ClosureReason.CAPTURE_MISSING, str(refusal))
        found = self.chain.day(road.underlying, session)
        if found is None or found.index_close is None:
            return _closed(road, session, ClosureReason.CAPTURE_MISSING, "no archived chain or index close")
        expiries = _recorded(found.expiries(road.expiry_kind), road.expiry_kind, session)
        if len(expiries) < EXPIRIES_RECORDED:
            return _closed(road, session, ClosureReason.EXPIRY_MISMATCH, f"{len(expiries)} {road.expiry_kind} expiries")
        lot = self._one_lot(found, expiries)
        if lot is None:
            return _closed(road, session, ClosureReason.LOT_MISMATCH, "no single dated lot for the expiries")
        steps = {e: strike_step((r.strike for r in found.rows_on(e)), found.index_close) for e in expiries}
        if None in steps.values():
            return _closed(road, session, ClosureReason.EXPIRY_MISMATCH, "an expiry lists fewer than two strikes")
        return RoadDay(road, session, expiries, lot, steps[expiries[0]], OPEN, steps)

    def _one_lot(self, found: DayChain, expiries: tuple[date, ...]) -> DatedLot | None:
        lots = [self.terms.lot(found, e) for e in expiries]
        if any(lot is None for lot in lots) or len({lot.units for lot in lots}) != 1:
            return None
        return lots[0]


def _recorded(listed: tuple[date, ...], kind: ExpiryKind, session: date) -> tuple[date, ...]:
    """A4 records monthlies from today on; A4f weeklies after today only (one expiring today has minutes left)."""
    live = [e for e in listed if (e > session if kind is ExpiryKind.WEEKLY else e >= session)]
    return tuple(live[:EXPIRIES_RECORDED])


def _closed(road: Road, session: date, reason: ClosureReason, detail: str) -> RoadDay:
    return RoadDay(road, session, (), None, None, RoadStatus(reason, detail))
