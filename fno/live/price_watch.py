"""Reads live prices every few seconds (Groww only) and turns sudden moves into shocks. A failing feed backs off
(20 s doubling to 15 minutes) and is reported once (retried until the alert is sent);
symbols the feed cannot price are logged once a day."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import asdict
from datetime import date, datetime, timedelta

from ..constants import EVENT_PRICE_SHOCK
from ..models import IST
from .feeds.live_prices import LivePriceSource
from .results_store import ResultsStore
from .shock_detector import Shock, ShockDetector

log = logging.getLogger(__name__)
FIRST_PAUSE_SECONDS = 20
MAX_PAUSE_SECONDS = 15 * 60
FEED_DOWN = "live price feed failing ({error}); sudden-move checks paused, retrying with back-off"
NOT_PRICED = "live price feed did not price: %s"


class PriceWatch:
    def __init__(self, source: LivePriceSource, detector: ShockDetector, store: ResultsStore):
        self.source, self.detector, self.store = source, detector, store
        self.failures = 0
        self.paused_until: datetime | None = None
        self._down_reported = False
        self._missing_logged: date | None = None

    def check(
        self, symbols: list[str], held: set[str], now: datetime, report: Callable[[datetime, str], bool]
    ) -> list[Shock]:
        """Shocks seen now (recorded as events); [] while paused or on failure."""
        if self.paused_until and now < self.paused_until:
            return []
        try:
            prices = self.source.prices(symbols)
        except Exception as exc:  # noqa: BLE001 - the 2-minute review still protects open trades
            self._back_off(now, exc, report)
            return []
        self.failures, self.paused_until, self._down_reported = 0, None, False
        missing = sorted(set(symbols) - set(prices))
        if missing and self._missing_logged != (today := now.astimezone(IST).date()):
            self._missing_logged = today
            log.warning(NOT_PRICED, ", ".join(missing))
        shocks = [shock for symbol, price in prices.items() if (shock := self.detector.observe(symbol, price, now))]
        for shock in shocks:
            self.store.record(EVENT_PRICE_SHOCK, {**asdict(shock), "held": shock.symbol in held}, now, shock.symbol)
        return shocks

    def _back_off(self, now: datetime, exc: Exception, report: Callable[[datetime, str], bool]) -> None:
        self.failures += 1
        pause = min(FIRST_PAUSE_SECONDS * 2 ** (self.failures - 1), MAX_PAUSE_SECONDS)
        self.paused_until = now + timedelta(seconds=pause)
        if not self._down_reported:  # retried on the next failure if the alert slot was taken
            self._down_reported = report(now, FEED_DOWN.format(error=exc))
