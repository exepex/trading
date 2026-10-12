"""Modelled option prices for the backtest: Black-Scholes with volatility from the underlying's own recent moves."""

from __future__ import annotations

from dataclasses import dataclass
from math import log, sqrt

from ..analytics import bs_price
from ..constants import INDEX_UNDERLYINGS

DAYS_PER_YEAR = 365.0
BARS_PER_SESSION = 75  # 5-minute bars, 09:15-15:30
INDEX_STRIKE_STEP = {"NIFTY": 50.0, "BANKNIFTY": 100.0, "FINNIFTY": 50.0}
STOCK_STRIKE_STEPS = ((250, 2.5), (500, 5.0), (1000, 10.0), (2500, 20.0), (5000, 50.0), (10000, 100.0))  # by price
LARGEST_STOCK_STEP = 250.0
MIN_SIGMA, MAX_SIGMA = 0.08, 1.5


@dataclass(frozen=True)
class OptionModel:
    days_to_expiry_at_entry: float = 10.0  # the desk buys options at least 4 and typically ~10 days out
    iv_over_realised: float = 1.1  # options usually price a little above realised volatility
    risk_free_rate: float = 0.065

    def sigma(self, closes: list[float]) -> float:
        """Annualised volatility from 5-minute closes (overnight gaps included), times the IV premium."""
        returns = [log(b / a) for a, b in zip(closes, closes[1:], strict=False) if a > 0 and b > 0]
        if len(returns) < 20:
            return 0.2
        mean = sum(returns) / len(returns)
        var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
        annual = sqrt(var * BARS_PER_SESSION * 252)
        return min(MAX_SIGMA, max(MIN_SIGMA, annual * self.iv_over_realised))

    def atm_strike(self, symbol: str, spot: float) -> float:
        """Nearest listed-style strike: index steps, or NSE-like steps by price band for stocks."""
        step = INDEX_STRIKE_STEP.get(symbol) if symbol in INDEX_UNDERLYINGS else None
        if step is None:
            step = next((size for limit, size in STOCK_STRIKE_STEPS if spot < limit), LARGEST_STOCK_STEP)
        return round(spot / step) * step

    def price(self, spot: float, strike: float, days_left: float, sigma: float, kind: str) -> float:
        years = max(days_left, 0.01) / DAYS_PER_YEAR
        return bs_price(spot, strike, years, self.risk_free_rate, sigma, kind)
