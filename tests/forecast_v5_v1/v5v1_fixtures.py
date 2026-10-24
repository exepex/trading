"""Real A16 and A16b rows (committed under research/data/intraday) for G14's tests, read through G7b's one candle
reader (`pack_wiring.candle_history`) as the package's wiring reads them."""

from __future__ import annotations

from datetime import date

from fno.forecast_v4_rules.pack_wiring import candle_history
from fno.forecast_v4_rules.series import SessionRv, live_intraday_rv
from fno.forecast_v5_v1.history import from_candle
from fno.intraday.rv_table import RvTable
from fno.intraday.wiring import INTRADAY_FOLDER


def candle_rows() -> list[SessionRv]:
    return from_candle(candle_history())


def live_rows() -> list[SessionRv]:
    return live_intraday_rv(RvTable(INTRADAY_FOLDER).rows())


def oct(day: int) -> date:
    return date(2026, 10, day)
