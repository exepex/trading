"""The times a named capture adds to its sidecar (story A4e; G10's pack needs every field's own times, protocol v4
section 1.6): each chain call's request and receive time (spot comes from it), the level reads' (India VIX and the
futures, one call), and A16's clock check before the first and after the last request. The default capture has no
log, so its sidecar stays A4's byte for byte."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from datetime import date, datetime

from ..intraday.clock import CLOCK_OK, CLOCK_PARTIAL, CLOCK_SKEW, CLOCK_UNCHECKED, ClockCheck, ClockReading
from ..models import OptionChain
from ..providers.base import Provider
from .market_levels import LevelSource, MarketLevels

SEVERITY = (CLOCK_OK, CLOCK_PARTIAL, CLOCK_SKEW, CLOCK_UNCHECKED)  # a missing reading counts as unchecked
READINGS = 2  # before the first request and after the last


class CaptureLog:
    """One attempt's times: `begin` before its first request, `finish` after its last (it returns the sidecar keys)."""

    def __init__(self, clock: ClockCheck, now: Callable[[], datetime]):
        self.clock, self.now = clock, now
        self.chains: list[dict] = []
        self.levels: dict = {}
        self.readings: list[ClockReading] = []

    def begin(self) -> None:
        self.chains, self.levels, self.readings = [], {}, []
        self._read()

    def chain(self, chain: OptionChain, sent: datetime, received: datetime) -> None:
        times = {"request_sent_at": sent.isoformat(), "response_received_at": received.isoformat()}
        self.chains.append({"expiry": chain.expiry.isoformat(), "spot": chain.spot, **times})

    def level_reads(self, sent: datetime, received: datetime) -> None:
        self.levels = {"levels_requested_at": sent.isoformat(), "levels_received_at": received.isoformat()}

    def finish(self) -> dict:
        self._read()
        statuses = [r.status for r in self.readings]
        worst = [r.worst for r in self.readings if r.worst is not None]
        return {
            "chains": self.chains, **self.levels, "clock_checks": statuses, "clock_status": _overall(statuses),
            "clock_worst_skew_seconds": max(worst) if worst else None,
        }  # fmt: skip

    def _read(self) -> None:
        """A check that fails is a missing reading, never a stopped capture: the status then cannot be clock_ok."""
        with suppress(Exception):
            self.readings.append(self.clock.check())


def _overall(statuses: list[str]) -> str:
    """clock_ok only when both readings are clock_ok; otherwise the worse one (a missing reading is unchecked)."""
    padded = statuses + [CLOCK_UNCHECKED] * (READINGS - len(statuses))
    return max(padded, key=SEVERITY.index)


class TimedProvider(Provider):
    """The capture's provider, unchanged, with each chain call's request and receive time written to the log."""

    def __init__(self, inner: Provider, log: CaptureLog):
        super().__init__({})  # lot sizes are never asked of the 3 pm recorder's provider
        self.inner, self.log = inner, log

    @property
    def name(self) -> str:
        return self.inner.name

    def expiries(self, underlying: str) -> list[date]:
        return self.inner.expiries(underlying)

    def chain(self, underlying: str, expiry: date) -> OptionChain:
        sent = self.log.now()
        chain = self.inner.chain(underlying, expiry)
        self.log.chain(chain, sent, self.log.now())
        return chain

    def quote_book(self, chain, strike, kind):
        return self.inner.quote_book(chain, strike, kind)


class TimedLevels(LevelSource):
    """The level source, unchanged, with the request and receive time of its one call (both NSE answers had arrived
    by the return, so the receive time is an honest upper bound for India VIX and for the futures)."""

    def __init__(self, inner: LevelSource, log: CaptureLog):
        self.inner, self.log, self.name = inner, log, inner.name

    def levels(self, underlying: str) -> MarketLevels:
        sent = self.log.now()
        levels = self.inner.levels(underlying)
        self.log.level_reads(sent, self.log.now())
        return levels
