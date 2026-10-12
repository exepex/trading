"""Spots sudden moves in an underlying from a stream of prices: the fastest sign that news has hit, often before any
headline. A shock is a move of at least the threshold between the extreme of the last window and now."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..constants import INDEX_UNDERLYINGS

PERCENT = 100.0


@dataclass(frozen=True)
class Shock:
    symbol: str
    move_pct: float  # + up, - down
    price: float
    at: datetime

    @property
    def direction(self) -> int:
        return 1 if self.move_pct > 0 else -1


@dataclass(frozen=True)
class ShockRules:
    window_seconds: float = 120.0
    index_move_pct: float = 0.4  # NIFTY moving 0.4% in two minutes is unusual
    stock_move_pct: float = 1.5
    cooldown_seconds: float = 600.0  # one alert per symbol per 10 minutes

    @classmethod
    def from_config(cls, cfg: dict | None) -> ShockRules:
        return cls(**{k: v for k, v in (cfg or {}).items() if k in cls.__dataclass_fields__})


class ShockDetector:
    def __init__(self, rules: ShockRules | None = None):
        self.rules = rules or ShockRules()
        self._prices: dict[str, deque[tuple[datetime, float]]] = {}
        self._last_shock: dict[str, datetime] = {}

    def observe(self, symbol: str, price: float, at: datetime) -> Shock | None:
        if price <= 0:
            return None
        window = self._prices.setdefault(symbol, deque())
        window.append((at, price))
        while window and at - window[0][0] > timedelta(seconds=self.rules.window_seconds):
            window.popleft()
        low, high = min(p for _, p in window), max(p for _, p in window)
        up, down = (price / low - 1) * PERCENT, (price / high - 1) * PERCENT
        move = up if abs(up) >= abs(down) else down
        limit = self.rules.index_move_pct if symbol in INDEX_UNDERLYINGS else self.rules.stock_move_pct
        last = self._last_shock.get(symbol)
        if abs(move) < limit or (last and at - last < timedelta(seconds=self.rules.cooldown_seconds)):
            return None
        self._last_shock[symbol] = at
        return Shock(symbol, round(move, 2), price, at)
