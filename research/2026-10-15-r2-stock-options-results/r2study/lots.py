"""Lot sizes (PROTOCOL.md section 3): the current format's column, or the legacy derivation with its validation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from datetime import date

from .bhav import DaySummary
from .rules import LOT_AGREEING_SESSIONS, LOT_VALIDATION_MIN_SHARE, LOT_WINDOW_SESSIONS
from .sessions import Sessions


def derived_lot(summary: DaySummary, symbol: str) -> int | None:
    """round(turnover / (contracts x settlement price)) of the near-month future; None without trades."""
    future = summary.near_future(symbol)
    if future is None or future.contracts <= 0 or future.settle <= 0:
        return None
    return round(future.turnover / (future.contracts * future.settle))


def column_lot(summary: DaySummary, symbol: str) -> int | None:
    future = summary.near_future(symbol)
    return future.lot if future is not None else None


def agreed_lot(values: list[int | None]) -> int | None:
    """The value derived on at least LOT_AGREEING_SESSIONS of the window's sessions, else None."""
    counts = Counter(v for v in values if v is not None)
    if not counts:
        return None
    value, seen = counts.most_common(1)[0]
    return value if seen >= LOT_AGREEING_SESSIONS else None


class LotSizes:
    """Lot size of a stock on a session. `current(day)` and `legacy(day)` give that session's summary in each format
    (None where the format has no file)."""

    def __init__(
        self,
        sessions: Sessions,
        current: Callable[[date], DaySummary | None],
        legacy: Callable[[date], DaySummary | None],
        legacy_valid: bool,
    ):
        self.sessions, self.current, self.legacy, self.legacy_valid = sessions, current, legacy, legacy_valid

    def derived(self, symbol: str, day: date) -> int | None:
        """The legacy rule: the agreed derived value over the LOT_WINDOW_SESSIONS sessions ending at `day`."""
        window = self.sessions.window_ending(day, LOT_WINDOW_SESSIONS)
        return agreed_lot([derived_lot(s, symbol) if (s := self.legacy(d)) else None for d in window])

    def lot(self, symbol: str, day: date) -> int | None:
        """The current format's column where the session has that file; else the legacy rule if it validated."""
        summary = self.current(day)
        if summary is not None:
            return column_lot(summary, symbol)
        return self.derived(symbol, day) if self.legacy_valid else None


def validate_derivation(
    sessions: Sessions,
    overlap: list[date],
    current: Callable[[date], DaySummary | None],
    legacy: Callable[[date], DaySummary | None],
) -> dict:
    """Share of stock-sessions on the overlap where the legacy rule gives exactly the current format's column."""
    rule = LotSizes(sessions, current, legacy, legacy_valid=True)
    matches = total = 0
    for day in overlap:
        summary = current(day)
        if summary is None or legacy(day) is None:
            continue
        for symbol in summary.futures:
            truth = column_lot(summary, symbol)
            if truth is None or not summary.is_fo_stock(symbol):
                continue
            total += 1
            matches += rule.derived(symbol, day) == truth
    share = matches / total if total else 0.0
    return {
        "stock_sessions": total,
        "exact_matches": matches,
        "share": share,
        "valid": total > 0 and share >= LOT_VALIDATION_MIN_SHARE,
    }
