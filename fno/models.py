"""Core data structures shared by providers, analytics and strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
EXPIRY_CLOSE = time(15, 30)


def now_ist() -> datetime:
    return datetime.now(IST)


@dataclass
class OptionQuote:
    strike: float
    kind: str  # "CE" or "PE"
    ltp: float
    bid: float | None = None
    ask: float | None = None
    oi: float = 0.0
    oi_change: float | None = None
    volume: float = 0.0
    iv: float | None = None  # percent, e.g. 12.5
    symbol: str | None = None

    @property
    def has_book(self) -> bool:
        return bool(self.bid and self.ask and self.bid > 0 and self.ask >= self.bid)

    @property
    def mid(self) -> float:
        if self.has_book:
            return (self.bid + self.ask) / 2
        return self.ltp

    @property
    def spread_pct(self) -> float | None:
        if not self.has_book or self.mid <= 0:
            return None
        return (self.ask - self.bid) / self.mid * 100

    def fill_price(self, side: str, slippage_pct: float = 0.5) -> float:
        """Conservative fill: buy at ask, sell at bid; LTP +/- slippage if no book."""
        if self.has_book:
            return self.ask if side == "buy" else self.bid
        adj = self.ltp * slippage_pct / 100
        return self.ltp + adj if side == "buy" else max(self.ltp - adj, 0.05)


@dataclass
class OptionChain:
    underlying: str
    spot: float
    expiry: date
    timestamp: datetime
    lot_size: int
    quotes: dict[tuple[float, str], OptionQuote] = field(default_factory=dict)
    source: str = ""

    def strikes(self) -> list[float]:
        return sorted({k for k, _ in self.quotes})

    def get(self, strike: float, kind: str) -> OptionQuote | None:
        return self.quotes.get((float(strike), kind))

    def atm_strike(self) -> float:
        return min(self.strikes(), key=lambda k: abs(k - self.spot))

    def strike_step(self) -> float:
        """Typical strike spacing near the money."""
        near = [k for k in self.strikes() if abs(k - self.spot) <= self.spot * 0.05]
        diffs = sorted(b - a for a, b in zip(near, near[1:]) if b > a)
        return diffs[len(diffs) // 2] if diffs else 50.0

    def years_to_expiry(self, at: datetime | None = None) -> float:
        at = at or self.timestamp
        if at.tzinfo is None:
            at = at.replace(tzinfo=IST)
        expiry_dt = datetime.combine(self.expiry, EXPIRY_CLOSE, tzinfo=IST)
        seconds = max((expiry_dt - at).total_seconds(), 3600.0)
        return seconds / (365.0 * 24 * 3600)

    def days_to_expiry(self, today: date | None = None) -> int:
        today = today or self.timestamp.date()
        return (self.expiry - today).days


@dataclass
class MarketContext:
    """Non-chain context for one underlying."""

    underlying: str
    spot: float
    prev_close: float | None = None
    closes: list[float] = field(default_factory=list)  # daily closes, oldest first
    vix: float | None = None
    vix_year_low: float | None = None
    vix_year_high: float | None = None

    @property
    def day_change_pct(self) -> float | None:
        if not self.prev_close:
            return None
        return (self.spot / self.prev_close - 1) * 100
