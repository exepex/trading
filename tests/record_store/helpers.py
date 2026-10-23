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
LEVELS = {"NIFTY 50": (22741.25, 22700.0), "NIFTY BANK": (54965.75, 54900.0), "INDIA VIX": (13.2, 13.5)}


def answer(stamp="23-Oct-2026 15:30", levels=None, **change) -> bytes:
    rows = [{"index": name, "last": last, "open": opened} for name, (last, opened) in (levels or LEVELS).items()]
    payload = {"timestamp": stamp, "data": rows, **change}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


class Official(OfficialCloses):
    def __init__(self, closes=None):
        self.found = closes

    def closes(self, day):
        return None if self.found is None else ("ind_close_all_23102026.csv", self.found)


OFFICIAL = {"Nifty 50": 22741.25, "Nifty Bank": 54965.75, "India VIX": 13.21}


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
        rules = ClosesRules(self.official)
        versions = ReceiptedFiles(self.receipts, a4h_raw_paths)
        return Certifier(rules, versions, self.drive, self.records, A4hRecordComparison(self.drive))
