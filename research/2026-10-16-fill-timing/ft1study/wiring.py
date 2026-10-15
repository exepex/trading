"""Composition root of study FT1: the panel, NSE's session calendar, India VIX, the A16b index candles in Drive, and
Groww's contract candles through A16's read-only client. No order code: the only Groww object is `ReadOnlyGroww`."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fno.config import load_app_config
from fno.intraday.read_only import ReadOnlyGroww
from fno.providers.groww import GrowwProvider
from fno.storage.wiring import build_session_calendar

from .candles import GrowwContractCandles
from .contracts import read_panel

IST = timezone(timedelta(hours=5, minutes=30))
PANEL_YEARS = (2024, 2025, 2026)
WINDOW_FIRST, WINDOW_LAST = date(2024, 1, 2), date(2026, 9, 30)


def now_ist() -> datetime:
    return datetime.now(IST)


def build_contract_candles() -> GrowwContractCandles:
    provider = GrowwProvider(load_app_config(None))
    return GrowwContractCandles(ReadOnlyGroww(lambda: provider.api), now_ist)  # the only Groww object it holds


def build_contracts():
    return read_panel(PANEL_YEARS)


def build_calendar():
    return build_session_calendar()


def sessions_before(calendar):
    def back(day: date, n: int) -> date:
        for _ in range(n):
            day = calendar.previous_session(day)
        return day

    return back


def window_expiries(contracts) -> list[date]:
    """Monthly expiries any decision day of the window can use (the last one lies after the window's end)."""
    later = [e for e in contracts.expiries if e > WINDOW_LAST]
    return [e for e in contracts.expiries if WINDOW_FIRST <= e <= WINDOW_LAST] + later[:1]
