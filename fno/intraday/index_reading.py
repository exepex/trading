"""The index level and Groww's own time for it (story A16, Definitions "Index source time").

1. Primary: the index quote's `last_price` with its `last_trade_time` (epoch seconds, or milliseconds above 10^11).
2. Fallback, when Groww leaves that time empty: the level AND its time from one record, the latest finished 1-minute
   index candle: its close, and its end (start + 60 s). The quote's price is then not used, so a frozen quote beside a
   live candle feed can never read as fresh. A candle still forming (end after our response) is never used.
3. Neither: no time; the caller marks the level stale.

Candle start times are IST wall-clock text with no offset (step 0: `2026-10-14T09:15:00`); they are read as naive ISO
and given +05:30 explicitly, never the host's zone. A time that carries an offset, or does not parse, raises
ValueError (the caller names it `index_parse`)."""

from __future__ import annotations

from datetime import datetime, timedelta

from ..models import IST

QUOTE_BASIS, CANDLE_BASIS = "quote_last_trade_time", "candle_1m_close"
CANDLE_SYMBOL = "NSE-NIFTY"
CANDLE_LOOKBACK = timedelta(minutes=5)
CANDLE_LENGTH = timedelta(minutes=1)
CANDLE_REQUEST_TIME = "%Y-%m-%d %H:%M:%S"
CLOSE = 4  # a candle row: start time, open, high, low, close, volume, open interest
MILLISECONDS_FROM = 10**11  # an epoch time above this is in milliseconds


def quote_reading(payload) -> tuple[float | None, datetime | None]:
    """The quote's level and its `last_trade_time` (None when Groww gives none)."""
    if not isinstance(payload, dict):
        return None, None
    level = payload.get("last_price")
    return (float(level) if level else None), epoch_time(payload.get("last_trade_time"))


def epoch_time(value) -> datetime | None:
    if not value:
        return None
    number = int(value)
    return datetime.fromtimestamp(number / 1000 if number > MILLISECONDS_FROM else number, IST)


def candle_window(received: datetime) -> dict:
    """The candle request's start and end times (IST text, as Groww takes them): the 5 minutes up to `received`."""
    local = received.astimezone(IST)
    return {
        "start_time": f"{local - CANDLE_LOOKBACK:{CANDLE_REQUEST_TIME}}",
        "end_time": f"{local:{CANDLE_REQUEST_TIME}}",
    }


def candle_reading(payload, received: datetime) -> tuple[float | None, datetime | None]:
    """The latest finished 1-minute candle's close and end time, or (None, None) when no candle has finished."""
    rows = payload.get("candles") if isinstance(payload, dict) else None
    finished = [(candle_start(row[0]) + CANDLE_LENGTH, row) for row in rows or []]
    finished = [(end, row) for end, row in finished if end <= received]
    if not finished:
        return None, None
    end, row = max(finished, key=lambda pair: pair[0])
    return float(row[CLOSE]), end


def candle_start(text: str) -> datetime:
    start = datetime.fromisoformat(text)
    if start.tzinfo is not None:
        raise ValueError("a candle time with an offset: the format changed, nothing is assumed")
    return start.replace(tzinfo=IST)
