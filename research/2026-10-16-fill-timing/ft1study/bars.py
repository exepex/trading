"""Groww's 15-minute candle rows as a lookup by candle start (PROTOCOL.md section 6). Rows are `[start time, open, high,
low, close, volume, open interest]`, the time an IST text without an offset (A16b's rule: an offset means the format
changed, so nothing is assumed). Copies are given earliest fetched first and the first copy's candle wins, as A16b's
index copies overlap."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from fno.intraday.index_reading import candle_start

CLOSE, VOLUME = 4, 5


@dataclass(frozen=True)
class Bar:
    close: float
    volume: float  # 0 when Groww gives none: a candle without a volume is never taken as traded

    @property
    def stale(self) -> bool:
        return self.volume <= 0


class BarBook:
    def __init__(self, copies: Iterable[list]):
        """`copies`: lists of Groww candle rows, earliest fetched first."""
        self._bars: dict[datetime, Bar] = {}
        for rows in copies:
            for row in rows:
                start = candle_start(str(row[0])).replace(tzinfo=None)
                self._bars.setdefault(start, _bar(row))

    def at(self, start: datetime) -> Bar | None:
        """The candle starting at `start` (naive IST), or None if Groww gave none."""
        return self._bars.get(start)

    def __len__(self) -> int:
        return len(self._bars)


def _bar(row: list) -> Bar:
    volume = row[VOLUME] if len(row) > VOLUME and row[VOLUME] is not None else 0
    return Bar(float(row[CLOSE]), float(volume))


class ArchivedPrices:
    """A contract's candle at a moment, from its archived copies only (each loaded once)."""

    def __init__(self, copies):
        """`copies(symbol)`: the symbol's candle-row lists, earliest fetched first (`ContractArchive.copies`)."""
        self.copies = copies
        self._books: dict[str, BarBook] = {}

    def bar(self, symbol: str, moment) -> Bar | None:
        if symbol not in self._books:
            self._books[symbol] = BarBook(self.copies(symbol))
        return self._books[symbol].at(moment.candle_start)
