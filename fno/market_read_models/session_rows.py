"""Reads one session's archived NSE files and computes its rows (story P6). Windows follow the W11 contract's
examples (a year and a week of equity and index files, three months of F&O files), but the sessions come from NSE's
calendar (SessionCalendar), never from weekdays. A missing file stops the build: a session is never built partly.
Reference lists use the copy archived on the session's day or the latest before it, else the nearest after it."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from ..research_data.calendar import SessionCalendar
from ..storage.raw_source import (
    NseDailyFoSource,
    NseDeliverySource,
    NseEquityBhavcopySource,
    NseIndexCloseSource,
)
from ..storage.raw_store import RawFileStore
from ..storage.snapshot_source import EquityListSource, Nifty500ListSource, SnapshotSource
from .blocks import SessionRows
from .fno_rows import FnoRowBuilder, UnderlyingDay, underlying_days
from .index_rows import index_rows, industries
from .nse_files import (
    read_delivery,
    read_equity_bhavcopy,
    read_equity_list,
    read_fo_rows,
    read_index_figures,
    read_nifty500_list,
)
from .stock_rows import UNIVERSE_NIFTY_500, stock_rows, stock_series

EQUITY_WINDOW = timedelta(days=372)  # the examples' window: a year of sessions (250) and a week to spare
INDEX_WINDOW = timedelta(days=372)
FNO_WINDOW = timedelta(days=95)  # three months of F&O files: the ATM IV's range
SNAPSHOT_SEARCH_DAYS = 10
READERS = 8  # files read at once from the archive


class IncompleteSession(RuntimeError):
    """A file the session needs is not archived; nothing is built."""

    def __init__(self, day: date, missing: list[str]):
        super().__init__(f"{day}: {len(missing)} archived file(s) missing, nothing built: {', '.join(missing[:5])}")
        self.missing = missing


class SessionRowsBuilder:
    def __init__(self, store: RawFileStore, calendar: SessionCalendar, fno: FnoRowBuilder):
        self.store, self.calendar, self.fno = store, calendar, fno

    def build(self, day: date) -> SessionRows:
        missing: list[str] = []
        equity = self._files(NseEquityBhavcopySource, day - EQUITY_WINDOW, day, missing)
        fo = self._files(NseDailyFoSource, day - FNO_WINDOW, day, missing)
        indices = self._files(NseIndexCloseSource, day - INDEX_WINDOW, day, missing)
        delivery = self._file(NseDeliverySource.path_for(day), missing)
        names, members = (self._snapshot(s, day, missing) for s in (EquityListSource, Nifty500ListSource))
        if missing:
            raise IncompleteSession(day, missing)
        names = read_equity_list(names, EquityListSource.FILENAME)
        history = self._fno_history(fo)
        stocks = stock_rows(
            stock_series(read_equity_bhavcopy(data, name) for _, name, data in equity),
            day,
            names,
            read_nifty500_list(members, Nifty500ListSource.FILENAME),
            read_delivery(delivery, NseDeliverySource.filename_for(day)),
            set(history),
        )
        figures = [(d, read_index_figures(data, name)) for d, name, data in indices]
        nifty_500 = [r for r in stocks if UNIVERSE_NIFTY_500 in r["u"]]
        return SessionRows(day, stocks, self.fno.rows(history, day, names), index_rows(figures), industries(nifty_500))

    def _files(self, source, start: date, end: date, missing: list[str]) -> list[tuple[date, str, bytes]]:
        days = self.calendar.sessions(start, end)
        with ThreadPoolExecutor(max_workers=READERS) as pool:
            files = list(pool.map(lambda d: self.store.get(source.path_for(d)), days))
        missing += [source.path_for(d) for d, data in zip(days, files) if data is None]
        return [(d, source.filename_for(d), data) for d, data in zip(days, files) if data is not None]

    def _file(self, path: str, missing: list[str]) -> bytes:
        data = self.store.get(path)
        if data is None:
            missing.append(path)
        return data

    def _snapshot(self, source: type[SnapshotSource], day: date, missing: list[str]) -> bytes | None:
        """The copy filed on `day` or the latest before it, else the nearest after it (a back-filled session)."""
        offsets = [-n for n in range(SNAPSHOT_SEARCH_DAYS + 1)] + list(range(1, SNAPSHOT_SEARCH_DAYS + 1))
        for offset in offsets:
            data = self.store.get(source.path_for(day + timedelta(days=offset)))
            if data is not None:
                return data
        missing.append(f"{source.dataset} (no copy within {SNAPSHOT_SEARCH_DAYS} days of {day})")
        return None

    @staticmethod
    def _fno_history(fo: list[tuple[date, str, bytes]]) -> dict[str, list[UnderlyingDay]]:
        history: dict[str, list[UnderlyingDay]] = {}
        for d, name, data in fo:
            for u in underlying_days(d, read_fo_rows(data, name)):
                history.setdefault(u.symbol, []).append(u)
        return history
