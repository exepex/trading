"""Market-data provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from ..models import MarketContext, OptionChain, OptionQuote

INDEX_NAMES = {
    "NIFTY": "NIFTY 50",
    "BANKNIFTY": "NIFTY BANK",
    "FINNIFTY": "NIFTY FINANCIAL SERVICES",
    "MIDCPNIFTY": "NIFTY MID SELECT",
}

YAHOO_SYMBOLS = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
    "MIDCPNIFTY": "NIFTY_MID_SELECT.NS",
}


def is_index(underlying: str) -> bool:
    return underlying.upper() in INDEX_NAMES


class Provider(ABC):
    name = "base"

    def __init__(self, config: dict):
        self.config = config

    def fallback_lot_size(self, underlying: str) -> int:
        return int(self.config.get("lot_sizes", {}).get(underlying.upper(), 1))

    @abstractmethod
    def expiries(self, underlying: str) -> list[date]:
        """Upcoming expiry dates, soonest first."""

    @abstractmethod
    def chain(self, underlying: str, expiry: date) -> OptionChain:
        """Full option chain for one expiry."""

    @abstractmethod
    def context(self, underlying: str) -> MarketContext:
        """Spot, price history and volatility context."""

    def live_quote(self, chain: OptionChain, strike: float, kind: str) -> OptionQuote | None:
        """The contract's current bid/ask when the chain itself has none (Groww's chain gives last price only).
        None when the provider cannot quote it; callers then fall back to last price +/- slippage."""
        return None
