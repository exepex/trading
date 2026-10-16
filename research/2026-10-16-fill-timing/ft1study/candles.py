"""15-minute candles of NIFTY option and future contracts, expired ones included (study FT1, PROTOCOL.md
section 17), behind `ContractCandles`. Groww is reached only through A16's `ReadOnlyGroww` (never the SDK client), one
call at a time and at least `MIN_GAP_SECONDS` apart (A16b's pacing). Any failure is `CandleCallFailed`, named by class
only: an exception's text could carry a credential."""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime

MIN_GAP_SECONDS = 0.5
DAY_FROM, DAY_TO = "09:00:00", "15:59:59"
CALL_TIMEOUT_SECONDS = 30
INTERVAL = "CANDLE_INTERVAL_MIN_15"  # the SDK's constant name


class CandleCallFailed(RuntimeError):
    """The call failed or its answer had no candle list."""


@dataclass(frozen=True)
class ContractAnswer:
    symbol: str
    start: date
    end: date
    raw: bytes  # the answer as received, serialised with sorted keys
    rows: list  # Groww's candle rows: [start time, open, high, low, close, volume, open interest]
    requested_at: datetime
    received_at: datetime


class ContractCandles(ABC):
    @abstractmethod
    def candles(self, symbol: str, start: date, end: date) -> ContractAnswer:
        """Every 15-minute candle of one contract from start to end (at most 90 days)."""


class GrowwContractCandles(ContractCandles):
    def __init__(self, api, clock: Callable[[], datetime], sleep=time.sleep, monotonic=time.monotonic):
        """`api`: A16's `ReadOnlyGroww`."""
        self.api, self.clock, self.sleep, self.monotonic = api, clock, sleep, monotonic
        self._last_start: float | None = None

    def candles(self, symbol: str, start: date, end: date) -> ContractAnswer:
        self._pace()
        requested = self.clock()
        try:
            answer = self.api.get_historical_candles(
                exchange=self.api.EXCHANGE_NSE, segment=self.api.SEGMENT_FNO, groww_symbol=symbol,
                start_time=f"{start} {DAY_FROM}", end_time=f"{end} {DAY_TO}",
                candle_interval=getattr(self.api, INTERVAL), timeout=CALL_TIMEOUT_SECONDS,
            )  # fmt: skip
            rows = answer.get("candles") if isinstance(answer, dict) else None
            raw = json.dumps(answer, sort_keys=True, separators=(",", ":")).encode()
        except Exception as exc:  # the SDK raises its own and requests' errors; the class name only
            raise CandleCallFailed(f"Groww {symbol} {start}..{end}: {type(exc).__name__}") from None
        if not isinstance(rows, list):
            raise CandleCallFailed(f"Groww {symbol} {start}..{end}: no candle list in the answer")
        return ContractAnswer(symbol, start, end, raw, rows, requested, self.clock())

    def _pace(self) -> None:
        now = self.monotonic()
        if self._last_start is not None and now - self._last_start < MIN_GAP_SECONDS:
            self.sleep(MIN_GAP_SECONDS - (now - self._last_start))
        self._last_start = self.monotonic()
