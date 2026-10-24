"""Synthetic chains for G13's tests: quotes priced by Black-76 at a given volatility (flat or a smile), with a chosen
spread, so the expected forward, IVs and distribution are known exactly."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from fno.price_distribution.chain import ChainDay, ChainSource, ExpiryChain, Quote
from fno.price_distribution.pricing import black76_price
from fno.price_distribution.store import DriveDistributionStore
from fno.storage.data_store import DataStore
from fno.storage.raw_store import RawFileConflict, RawFileStore
from fno.storage.receipts import ReceiptFolder

DAY = date(2026, 10, 16)
NEAR, NEXT = date(2026, 10, 27), date(2026, 11, 23)
RATE = 0.065
FORWARD = 23_000.0


def flat(sigma: float) -> Callable[[float], float]:
    return lambda strike: sigma


def quotes(forward: float, expiry: date, vol: Callable[[float], float], strikes, half_spread: float = 0.05,
           day: date = DAY) -> tuple[Quote, ...]:  # fmt: skip
    days = (expiry - day).days
    found = []
    for strike in strikes:
        for kind in ("CE", "PE"):
            mid = black76_price(forward, strike, kind, days, RATE, vol(strike))
            found.append(
                Quote(strike, kind, mid, mid - half_spread, mid + half_spread, True, None, f"{kind}{strike:g}")
            )
    return tuple(found)


def strikes(low: float = 20_800, high: float = 25_200, step: float = 50) -> list[float]:
    return [low + step * i for i in range(int((high - low) / step) + 1)]


def expiry_chain(expiry: date = NEAR, vol=None, forward: float = FORWARD, grid=None, future=None) -> ExpiryChain:
    return ExpiryChain(expiry, quotes(forward, expiry, vol or flat(0.12), grid or strikes()), future)


def chain_day(expiries=None, underlying: str = "NIFTY", spot: float | None = 22_990.0, day: date = DAY) -> ChainDay:
    found = expiries if expiries is not None else (expiry_chain(NEAR), expiry_chain(NEXT, forward=23_100.0))
    return ChainDay(underlying, day, "nse", "nifty_20261016_145500", "ab" * 32, "2026-10-16T14:55:24+05:30", spot,
                    tuple(found))  # fmt: skip


class MemoryDrive(RawFileStore):
    """Drive's write-once rule in memory: same bytes again are a no-op, other bytes a conflict; `fail` refuses puts."""

    def __init__(self, fail: bool = False):
        self.files, self.fail = {}, fail

    def get(self, path: str) -> bytes | None:
        return self.files.get(path)

    def put(self, path: str, data: bytes) -> None:
        if self.fail:
            raise RuntimeError("Drive is down")
        if path in self.files and self.files[path] != data:
            raise RawFileConflict(path)
        self.files[path] = data


def drive_store(tmp_path, fail: bool = False) -> tuple[DriveDistributionStore, MemoryDrive, ReceiptFolder]:
    drive, receipts = MemoryDrive(fail), ReceiptFolder(tmp_path / "receipts")
    return DriveDistributionStore(drive, DataStore(drive, "data", receipts, "pricedist", "run-1")), drive, receipts


class Chains(ChainSource):
    """A fixed chain per (underlying, day); a value that is an exception is raised."""

    def __init__(self, chains: dict):
        self.chains, self.calls = chains, []

    def chain(self, underlying, day):
        self.calls.append((underlying, day))
        found = self.chains.get((underlying, day))
        if isinstance(found, Exception):
            raise found
        return found
