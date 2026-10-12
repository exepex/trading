"""Option-price history: one at-the-money implied volatility (IV) per underlying per day, and where today's IV sits
in its own range (IV rank, 0 = cheapest seen, 100 = dearest). Option buyers want low IV rank: rich options lose value
when volatility falls back (IV crush) even if the price moves the right way."""

from __future__ import annotations

import threading
from datetime import date, datetime, timedelta

from ...analytics import atm_iv
from ...constants import EVENT_IV_SNAPSHOT
from ...models import IST, OptionChain
from ..results_store import ResultsStore

DEFAULT_MIN_DAYS = 60  # fewer days of history and the rank means little
DEFAULT_LOOKBACK_DAYS = 365
PERCENT = 100.0


class IvHistory:
    def __init__(
        self,
        store: ResultsStore,
        min_days: int = DEFAULT_MIN_DAYS,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        risk_free_rate: float = 0.065,
    ):
        self.store = store
        self.min_days = min_days
        self.lookback_days = lookback_days
        self.risk_free_rate = risk_free_rate
        self._today: dict[str, float] = {}  # latest ATM IV seen today, per underlying
        self._past: dict[str, dict[str, float]] | None = None  # symbol -> {day: iv}, loaded once
        self._lock = threading.Lock()

    def observe(self, symbol: str, chain: OptionChain) -> float | None:
        """Remember the latest ATM IV of a chain the desk read. Returns it as a percentage."""
        iv = atm_iv(chain, self.risk_free_rate)
        if iv is None or iv <= 0:
            return None
        with self._lock:
            self._today[symbol] = round(iv * PERCENT, 2)
        return self._today[symbol]

    def flush(self, now: datetime) -> int:
        """Store today's latest ATM IV for every underlying seen (once, after the close). Returns how many."""
        day = now.astimezone(IST).date().isoformat()
        with self._lock:
            today, self._today = self._today, {}
        for symbol, iv in sorted(today.items()):
            self.store.record(EVENT_IV_SNAPSHOT, {"symbol": symbol, "day": day, "atm_iv": iv}, now, symbol)
            if self._past is not None:
                self._past.setdefault(symbol, {})[day] = iv
        return len(today)

    def rank(self, symbol: str, iv: float | None, today: date) -> float | None:
        """0-100 position of `iv` (percent) between the stored low and high, or None without enough history."""
        if iv is None:
            return None
        past = {d: v for d, v in self._history(today).get(symbol, {}).items() if d < today.isoformat()}
        if len(past) < self.min_days:
            return None
        low, high = min(past.values()), max(past.values())
        if high <= low:
            return None
        return round(max(0.0, min(PERCENT, (iv - low) / (high - low) * PERCENT)), 1)

    def _history(self, today: date) -> dict[str, dict[str, float]]:
        with self._lock:
            if self._past is None:
                since = today - timedelta(days=self.lookback_days)
                self._past = {}
                for snap in self.store.payloads(EVENT_IV_SNAPSHOT, since):
                    self._past.setdefault(snap["symbol"], {})[snap["day"]] = float(snap["atm_iv"])
            return self._past
