"""The checks on the day's market data (story C3): the spot in the pack is within `limit` of the previous session's
official close unless the day is flagged as a shock, and the previous session's NSE F&O file is archived (session per
the A7 calendar). A wrong spot makes the snapshot's prices suspect; a missing NSE file stops new trades only."""

from __future__ import annotations

from collections.abc import Sequence

from ..research_data.calendar import SessionCalendar
from ..storage.raw_source import NseArchiveSource
from ..storage.raw_store import RawFileStore
from .data_checks import CheckSubject, DataCheck
from .shock import ShockFlags

SPOT_LIMIT = 0.02  # story C3: spot within 2% of the previous close
ROUNDING = 1e-9  # float rounding of the ratio: exactly 2% passes
OPTION_PREFIX, CLOSE_PREFIX = "option:", "close:"


def pack_items(subject: CheckSubject, prefix: str) -> dict[str, object]:
    return {i["name"]: i["value"] for i in subject.pack.body["items"] if i["name"].startswith(prefix)}


class SpotNearPreviousClose(DataCheck):
    name, prices_unverified = "spot", True

    def __init__(self, calendar: SessionCalendar, shocks: ShockFlags, limit: float = SPOT_LIMIT):
        self.calendar, self.shocks, self.limit = calendar, shocks, limit

    def problems(self, subject: CheckSubject) -> list[str]:
        spots = {v["spot"] for v in pack_items(subject, OPTION_PREFIX).values() if v.get("spot")}
        previous = self.calendar.previous_session(subject.day)
        close = pack_items(subject, CLOSE_PREFIX).get(f"{CLOSE_PREFIX}{previous.isoformat()}")
        if len(spots) != 1:
            return [f"the pack holds {len(spots)} different spot values, not one"]
        if not close or not close.get("nifty"):
            return [f"the pack holds no official close of the previous session {previous}"]
        spot, previous_close = spots.pop(), close["nifty"]
        move = spot / previous_close - 1
        if abs(move) <= self.limit + ROUNDING or self.shocks.flagged(subject.day):
            return []
        return [
            f"spot {spot:,.2f} is {move:+.2%} from the previous close {previous_close:,.2f} ({previous}), beyond "
            f"{self.limit:.0%}, and the day is not flagged as a shock ({self.shocks.source})"
        ]


class PreviousSessionFile(DataCheck):
    name, prices_unverified = "previous NSE file", False

    def __init__(self, stores: Sequence[RawFileStore], source: type[NseArchiveSource], calendar: SessionCalendar):
        self.stores, self.source, self.calendar = tuple(stores), source, calendar

    def problems(self, subject: CheckSubject) -> list[str]:
        previous = self.calendar.previous_session(subject.day)
        path = self.source.path_for(previous)
        if any(store.get(path) is not None for store in self.stores):
            return []
        return [f"NSE's file of the previous session {previous} is not archived ({path})"]
