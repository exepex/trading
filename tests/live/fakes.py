"""Test doubles for the live desk: deterministic feeds and a capturing Slack sink."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from fno.live.feeds.nse_feed import OpenInterestMove
from fno.live.feeds.price_feed import DayQuote, IntradayPriceFeed
from fno.live.models import Candle
from fno.models import IST

SESSION_DAY = date(2026, 10, 12)  # a Monday


def at(hour: int, minute: int, day: date = SESSION_DAY) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=IST)


def trending_candles(start_price: float, step_pct: float, count: int, day: date = SESSION_DAY) -> list[Candle]:
    """5-minute candles from 09:15 moving steadily by step_pct each bar."""
    candles, price = [], start_price
    for i in range(count):
        nxt = price * (1 + step_pct / 100)
        candles.append(
            Candle(
                at(9, 15, day) + timedelta(minutes=5 * i),
                price,
                max(price, nxt) * 1.0005,
                min(price, nxt) * 0.9995,
                nxt,
                1000,
            )
        )
        price = nxt
    return candles


class FakePriceFeed(IntradayPriceFeed):
    def __init__(self, quotes: dict[str, DayQuote], candles: dict[str, list[Candle]]):
        self.quotes, self._candles = quotes, candles

    def day_quotes(self, symbols):
        return {s: q for s, q in self.quotes.items() if s in symbols}

    def candles(self, symbol):
        return self._candles.get(symbol, [])


class FakeNseFeed:
    def __init__(self, oi_moves: dict[str, OpenInterestMove], lot_sizes: dict[str, int], banned=frozenset()):
        self.oi_moves, self._lots, self._banned = oi_moves, lot_sizes, set(banned)

    def open_interest_moves(self):
        return self.oi_moves

    def lot_sizes(self):
        return self._lots

    def ban_list(self):
        return self._banned

    def trading_holidays(self):
        return set()


class CapturingAlerts:
    def __init__(self):
        self.messages: list[str] = []

    def send(self, text: str) -> bool:
        self.messages.append(text)
        return True

    def problem(self, message: str) -> bool:
        return self.send(f"problem: {message}")

    def kill_switch(self) -> bool:
        return self.send("kill switch")
