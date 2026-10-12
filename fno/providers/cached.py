"""Short-lived cache in front of any provider, so one chain serves the scan, both paper books and every trade on it."""

from __future__ import annotations

import threading
import time
from datetime import date

from ..models import MarketContext, OptionChain, OptionQuote
from .base import Provider

DEFAULT_CHAIN_MAX_AGE_SECONDS = 50  # just under the fastest review interval: every review still sees a fresh quote


class CachedProvider(Provider):
    def __init__(self, inner: Provider, chain_max_age_seconds: float = DEFAULT_CHAIN_MAX_AGE_SECONDS, clock=None):
        super().__init__(inner.config)
        self.inner = inner
        self.name = inner.name
        self.chain_max_age_seconds = chain_max_age_seconds
        self.clock = clock or time.monotonic
        self._chains: dict[tuple[str, date], tuple[float, OptionChain]] = {}
        self._expiries: dict[tuple[str, date], list[date]] = {}
        self._lock = threading.Lock()

    def expiries(self, underlying: str) -> list[date]:
        key = (underlying, date.today())
        if key not in self._expiries:
            self._expiries[key] = self.inner.expiries(underlying)
        return self._expiries[key]

    def chain(self, underlying: str, expiry: date) -> OptionChain:
        key = (underlying, expiry)
        with self._lock:
            cached = self._chains.get(key)
            if cached and self.clock() - cached[0] < self.chain_max_age_seconds:
                return cached[1]
        chain = self.inner.chain(underlying, expiry)
        with self._lock:
            self._chains[key] = (self.clock(), chain)
        return chain

    def context(self, underlying: str) -> MarketContext:
        return self.inner.context(underlying)

    def live_quote(self, chain: OptionChain, strike: float, kind: str) -> OptionQuote | None:
        return self.inner.live_quote(chain, strike, kind)  # never cached: it is the price we trade at
