"""Lot sizes (PROTOCOL.md section 3; amendment 1 D4, revision 1): the lot of the contract traded. Current format: the
chosen expiry's own option rows. Legacy format: the derivation on the stock future of the same expiry, used only if it
matched the current format's column on the overlap."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from datetime import date

from .bhav import Chain, DaySummary
from .rules import LOT_AGREEING_SESSIONS, LOT_VALIDATION_MIN_SHARE, LOT_WINDOW_SESSIONS
from .sessions import Sessions


def derived_lot(summary: DaySummary, symbol: str, expiry: date) -> int | None:
    """round(turnover / (contracts x settlement price)) of the same-expiry future; None without trades."""
    future = summary.future(symbol, expiry)
    if future is None or future.contracts <= 0 or future.settle <= 0:
        return None
    return round(future.turnover / (future.contracts * future.settle))


def agreed_lot(values: list[int | None]) -> int | None:
    """The value derived on at least LOT_AGREEING_SESSIONS of the window's sessions, else None."""
    counts = Counter(v for v in values if v is not None)
    if not counts:
        return None
    value, seen = counts.most_common(1)[0]
    return value if seen >= LOT_AGREEING_SESSIONS else None


def chain_lot(chain: Chain, k0: float) -> int | None:
    """The lot column of the expiry's K0 call, else its K0 put (current format only)."""
    for kind in ("CE", "PE"):
        leg = chain.get((k0, kind))
        if leg is not None and leg.lot:
            return leg.lot
    return None


class LegacyLots:
    """The protocol's legacy rule on the same-expiry future: the agreed derived value over the LOT_WINDOW_SESSIONS
    sessions ending at a session. `legacy(day)` is that session's legacy-format summary (None if none)."""

    def __init__(self, sessions: Sessions, legacy: Callable[[date], DaySummary | None]):
        self.sessions, self.legacy = sessions, legacy

    def derived(self, symbol: str, day: date, expiry: date) -> int | None:
        window = self.sessions.window_ending(day, LOT_WINDOW_SESSIONS)
        return agreed_lot([derived_lot(s, symbol, expiry) if (s := self.legacy(d)) else None for d in window])


def validate_derivation(
    sessions: Sessions,
    overlap: list[date],
    current: Callable[[date], DaySummary | None],
    legacy: Callable[[date], DaySummary | None],
) -> dict:
    """Share of stock-sessions on the overlap where the legacy rule, on the near-month future, gives exactly that
    future's lot column in the current format."""
    rule = LegacyLots(sessions, legacy)
    matches = total = 0
    for day in overlap:
        summary = current(day)
        if summary is None or legacy(day) is None:
            continue
        for symbol in summary.futures:
            future = summary.near_future(symbol)
            if future is None or future.lot is None or not summary.is_fo_stock(symbol):
                continue
            total += 1
            matches += rule.derived(symbol, day, future.expiry) == future.lot
    share = matches / total if total else 0.0
    return {
        "stock_sessions": total,
        "exact_matches": matches,
        "share": share,
        "valid": total > 0 and share >= LOT_VALIDATION_MIN_SHARE,
    }
