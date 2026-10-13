"""Archives today's copy of an NSE reference list (story P6): fetched, checked, saved under the day's folder with its
manifest row (through the archive store). A copy already archived for the day is kept; a different one is refused."""

from __future__ import annotations

from datetime import date

from .coverage import Validator
from .raw_source import NseArchiveSource
from .raw_store import RawFileStore

TAKEN = "{path}: archived ({size} bytes)"
ALREADY = "{path}: already archived for this day"
NOT_SERVED = "{path}: NSE does not serve it now"


class SnapshotTaker:
    def __init__(self, store: RawFileStore, source: NseArchiveSource, validate: Validator):
        self.store, self.source, self.validate = store, source, validate

    def take(self, day: date) -> str:
        """One line saying what happened; ValueError when NSE's copy fails its check (nothing is saved)."""
        path = self.source.path_for(day)
        if self.store.get(path) is not None:
            return ALREADY.format(path=path)
        data = self.source.fetch(path)
        if data is None:
            return NOT_SERVED.format(path=path)
        self.validate(self.source.FILENAME, data)
        self.store.put(path, data)
        return TAKEN.format(path=path, size=len(data))
