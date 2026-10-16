"""What the monitor reads about one A16 mark (story LM1): the mark's status and index level, the latest mark it could
check (from A16's ledger, so a mark another run stored counts too), the clock skew A16 measured, and NSE's close of the
previous session (the archived index-close file, the official close; None when it is not archived yet)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime

from ..constants import INDEX_NIFTY_50
from ..intraday.document import SnapshotDocument, parse_time
from ..intraday.ledger import SlotLedger
from ..market_read_models.nse_files import read_index_figures
from ..research_data.calendar import SessionCalendar
from ..storage.raw_source import NseIndexCloseSource
from ..storage.raw_store import RawFileStore
from .model import MonitorMark
from .settings import MonitorSettings


class PreviousCloses(ABC):
    @abstractmethod
    def close(self, day: date) -> float | None:
        """NIFTY 50's close of `day`; None when it is not known yet."""


class ArchivedNiftyCloses(PreviousCloses):
    def __init__(self, raw: RawFileStore):
        self.raw = raw

    def close(self, day: date) -> float | None:
        data = self.raw.get(NseIndexCloseSource.path_for(day))
        if data is None:
            return None
        nifty = read_index_figures(data, NseIndexCloseSource.filename_for(day)).get(INDEX_NIFTY_50)
        return nifty.close if nifty else None


class MarkReader:
    def __init__(
        self, ledger: SlotLedger, closes: PreviousCloses, calendar: SessionCalendar, settings: MonitorSettings
    ):
        self.ledger, self.closes, self.calendar, self.settings = ledger, closes, calendar, settings

    def read(self, day: date, mark: datetime, document: SnapshotDocument | None, status: str) -> MonitorMark:
        usable = self.settings.usable_statuses
        level = document.index_level if document is not None and status in usable else None
        rows = self.ledger.rows(day)
        good = [parse_time(r["mark"]) for r in rows if r["status"] in usable and parse_time(r["mark"]) <= mark]
        if level is None:
            good = [m for m in good if m != mark]  # this mark was not checked here, so it does not reset the clock
        own = next((r for r in rows if parse_time(r["mark"]) == mark), {})
        skew = own.get("clock_skew_seconds") or None
        previous = self.closes.close(self.calendar.previous_session(day))
        return MonitorMark(day, mark, status, level, previous, max(good, default=None),
                           float(skew) if skew else None)  # fmt: skip
