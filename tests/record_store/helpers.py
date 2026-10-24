"""Story DR1's test world: O9's real `DataStore` and `ReceiptFolder` over a local Drive folder, A4h's raw answers
saved the way A4h saves them, and an official index-close file stand-in."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

from fno.close_read.official import OfficialCloses
from fno.close_read.records import raw_path
from fno.record_store.certifier import Certifier
from fno.record_store.closes import A4hRecordComparison, ClosesRules, a4h_raw_paths
from fno.record_store.record_folder import RecordFolder
from fno.record_store.staging import ReceiptedFiles
from fno.storage.data_store import DataStore
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipts import ReceiptFolder

DAY = date(2026, 10, 23)
SESSION = DAY.isoformat()
PREVIOUS_DAY = date(2026, 10, 22)
LEVELS = {"NIFTY 50": (22741.25, 22700.0), "NIFTY BANK": (54965.75, 54900.0), "INDIA VIX": (13.2, 13.5)}
RANGE = {"NIFTY 50": (22760.0, 22690.0), "NIFTY BANK": (55010.0, 54880.0), "INDIA VIX": (13.9, 13.0)}  # high, low
PREVIOUS_CLOSE = {"NIFTY 50": 22712.4, "NIFTY BANK": 54920.1, "INDIA VIX": 13.4}
OFFICIAL_NAME = {"NIFTY 50": "Nifty 50", "NIFTY BANK": "Nifty Bank", "INDIA VIX": "India VIX"}


def answer(stamp="23-Oct-2026 15:30", levels=None, ranges=None, previous=None, **change) -> bytes:
    """NSE's index list as A4h saves it (A4h-2's fields: high, low and previousClose for every index)."""
    levels, ranges, previous = levels or LEVELS, {**RANGE, **(ranges or {})}, {**PREVIOUS_CLOSE, **(previous or {})}
    rows = [{"index": name, "last": last, "open": opened, "high": ranges[name][0], "low": ranges[name][1],
             "previousClose": previous[name]} for name, (last, opened) in levels.items()]  # fmt: skip
    payload = {"timestamp": stamp, "data": rows, **change}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def official_values(closes=None, ranges=None) -> dict:
    """NSE's index-close file as `OfficialCloses.values` gives it: open, high, low and close by official name."""
    closes, ranges = {**{n: v[0] for n, v in LEVELS.items()}, **(closes or {})}, {**RANGE, **(ranges or {})}
    return {OFFICIAL_NAME[name]: {"open": LEVELS[name][1], "high": ranges[name][0], "low": ranges[name][1],
                                  "close": closes[name]} for name in LEVELS}  # fmt: skip


PREVIOUS_OFFICIAL = {
    OFFICIAL_NAME[n]: {"open": None, "high": None, "low": None, "close": c} for n, c in PREVIOUS_CLOSE.items()
}


class Official(OfficialCloses):
    """The official files of the day and of the previous session (None: not archived yet)."""

    def __init__(self, today=None, previous=PREVIOUS_OFFICIAL):
        self.files = {DAY: today, PREVIOUS_DAY: previous}

    def values(self, day):
        found = self.files.get(day)
        return None if found is None else (f"ind_close_all_{day:%d%m%Y}.csv", found)


OFFICIAL = official_values()


class World:
    def __init__(self, tmp: Path, official: OfficialCloses | None = None):
        self.drive = LocalFolderStore(tmp / "drive")
        self.receipts = ReceiptFolder(tmp / "receipts")
        self.store = DataStore(self.drive, "data", self.receipts, "closeread", "run-1",
                               clock=lambda: datetime(2026, 10, 23, 10, 10, tzinfo=UTC))  # fmt: skip
        self.records = RecordFolder(tmp / "records")
        self.official = official or Official(OFFICIAL)

    def a4h_saves(self, which: str, data: bytes) -> None:
        self.store.put(raw_path(DAY, which), data)

    def a4h_records(self, document: dict) -> None:
        self.store.put(f"closes/2026/10/{SESSION}.json", json.dumps(document).encode())

    def certifier(self) -> Certifier:
        rules = ClosesRules(self.official, lambda day: PREVIOUS_DAY)
        versions = ReceiptedFiles(self.receipts, a4h_raw_paths)
        return Certifier(rules, versions, self.drive, self.records, A4hRecordComparison(self.drive))
