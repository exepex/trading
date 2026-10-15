"""The fetch (PROTOCOL.md section 17): each planned contract window once, through the paced read-only candle source,
archived to Drive with its manifest row. Windows already held are skipped, so a stopped fetch resumes. A failed call is
retried once after the whole plan; a window still failing is listed, and its legs are missing in the analysis. Nothing
is fetched during market hours (09:00-15:45 IST on a session day)."""

from __future__ import annotations

import time as clock_time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, time

from fno.research_data.calendar import SessionCalendar

from .archive import ContractArchive
from .candles import CandleCallFailed, ContractCandles
from .plan import FetchItem

MARKET_FROM, MARKET_TO = time(9, 0), time(15, 45)


class MarketOpen(RuntimeError):
    """The fetch stopped: it is market hours on a session day."""


class MarketHours:
    def __init__(self, calendar: SessionCalendar, now: Callable[[], datetime]):
        self.calendar, self.now = calendar, now

    def open_now(self) -> bool:
        now = self.now()
        return self.calendar.is_session(now.date()) and MARKET_FROM <= now.time() < MARKET_TO


@dataclass
class FetchReport:
    planned: int
    already_held: int = 0
    fetched: int = 0
    failed: list[FetchItem] = field(default_factory=list)
    seconds: float = 0.0

    def line(self) -> str:
        rate = f"{self.seconds / self.fetched:.2f} s a call" if self.fetched else "no call"
        return (f"planned {self.planned}, already held {self.already_held}, fetched {self.fetched}, "
                f"failed {len(self.failed)}, {self.seconds:.0f} s ({rate})")  # fmt: skip


class Fetcher:
    def __init__(self, source: ContractCandles, archive: ContractArchive, hours: MarketHours,
                 monotonic: Callable[[], float] = clock_time.monotonic):  # fmt: skip
        self.source, self.archive, self.hours, self.monotonic = source, archive, hours, monotonic

    def run(self, items: Sequence[FetchItem]) -> FetchReport:
        todo = [i for i in items if not self.archive.held(i.symbol, i.start, i.end)]
        report = FetchReport(len(items), already_held=len(items) - len(todo))
        started = self.monotonic()
        try:
            report.failed = self._pass(self._pass(todo, report), report)
        finally:
            report.seconds = self.monotonic() - started
        return report

    def _pass(self, items: Sequence[FetchItem], report: FetchReport) -> list[FetchItem]:
        failed = []
        for item in items:
            if self.hours.open_now():
                raise MarketOpen(f"market hours: stopped after {report.fetched} calls; run again after 15:45 IST")
            try:
                answer = self.source.candles(item.symbol, item.start, item.end)
            except CandleCallFailed:
                failed.append(item)
                continue
            self.archive.save(item.expiry, answer)
            report.fetched += 1
        return failed
