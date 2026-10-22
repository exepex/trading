"""The dated lot of a road from A20a's archived NSE market-lot file (`fo_mktlots.csv`, one copy per session day)."""

import csv
from datetime import date

from ...research_data.fo_masters import BadFile, read_lot_sizes
from ...storage.raw_library import RawFileLibrary
from ...storage.snapshot_source import FoLotSizeSource
from ..contracts.roads import DatedLot

MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")


def month_label(expiry: date) -> str:
    """The column NSE's lot file uses for an expiry month, e.g. `OCT-26` (never locale dependent)."""
    return f"{MONTHS[expiry.month - 1]}-{expiry:%y}"


class ArchivedLots:
    """Reads the session's own copy of the lot file from stored files; a session with no copy has no lot (a lot is
    never carried over from another day)."""

    def __init__(self, library: RawFileLibrary):
        self.library = library

    def lot(self, underlying: str, session: date, expiries: tuple[date, ...]) -> DatedLot | None:
        path = FoLotSizeSource.path_for(session)
        found = self.library.get(path).data
        if found is None:
            return None
        try:
            by_month = read_lot_sizes(found, FoLotSizeSource.FILENAME).get(underlying, {})
        except (BadFile, UnicodeDecodeError, csv.Error):
            return None
        units = {by_month.get(month_label(expiry)) for expiry in expiries}
        if len(units) != 1 or None in units or min(units) <= 0:
            return None
        return DatedLot(units.pop(), path)
