"""Pure intraday calculations on 5-minute candles."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from ..analytics import ema
from .models import Candle

MARKET_OPEN = time(9, 15)


def clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def vwap(candles: list[Candle]) -> float | None:
    """Volume-weighted average price since the open (typical price per candle)."""
    volume = sum(c.volume for c in candles)
    if volume <= 0:
        return None
    return sum((c.high + c.low + c.close) / 3 * c.volume for c in candles) / volume


def opening_range(candles: list[Candle], minutes: int) -> tuple[float, float] | None:
    """High and low of the first `minutes` of the session, once that window has closed."""
    if not candles:
        return None
    session_open = datetime.combine(candles[0].start.date(), MARKET_OPEN, tzinfo=candles[0].start.tzinfo)
    window_end = session_open + timedelta(minutes=minutes)
    window = [c for c in candles if c.start < window_end]
    if not window or candles[-1].start < window_end:
        return None
    return max(c.high for c in window), min(c.low for c in window)


def ema_gap_pct(closes: list[float], fast: int, slow: int) -> float | None:
    """Fast EMA minus slow EMA, as % of price: positive in an uptrend."""
    if len(closes) < slow:
        return None
    fast_value, slow_value = ema(closes, fast)[-1], ema(closes, slow)[-1]
    return (fast_value - slow_value) / closes[-1] * 100


def change_pct(start: float, end: float) -> float:
    return (end / start - 1) * 100 if start else 0.0
