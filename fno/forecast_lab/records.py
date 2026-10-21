"""The 15:45 report's records in O9's data store (story FL1-1): the report (text and alerts) and its posted marker,
each a write-once JSON file in Drive's data area with its receipt under `receipts/`. A report is read back verified
against its receipt's SHA-256 (the Drive cache's check, for one file; the cache syncs whole folders): a missing or
damaged copy stops the run, never a silent rebuild."""

from __future__ import annotations

import hashlib
import json
from datetime import date

from ..storage.data_store import DataStore
from ..storage.receipts import ReceiptFolder
from .constants import REPORT_AREA
from .lab_close import ReportRecords

UNREADABLE = "the written 15:45 report of {day} cannot be read back verified: {problems}"


class DriveReportRecords(ReportRecords):
    def __init__(self, store: DataStore, receipts: ReceiptFolder):
        self.store, self.receipts = store, receipts

    @staticmethod
    def _path(day: date, suffix: str = "") -> str:
        return f"{REPORT_AREA}/{day:%Y}/{day.isoformat()}{suffix}.json"

    def _drive_path(self, path: str) -> str:
        return f"{self.store.area}/{path}"

    def report(self, day: date) -> tuple[str, list[str]] | None:
        drive_path = self._drive_path(self._path(day))
        receipt = self.receipts.read(drive_path)
        if receipt is None:
            return None
        data = self.store.drive.get(drive_path)
        if data is None or hashlib.sha256(data).hexdigest() != receipt.sha256:
            raise RuntimeError(UNREADABLE.format(day=day, problems="missing" if data is None else "damaged"))
        body = json.loads(data)
        return body["text"], list(body["alerts"])

    def write_report(self, day: date, text: str, alerts: list[str]) -> None:
        self.store.put(self._path(day), _json({"day": day.isoformat(), "text": text, "alerts": list(alerts)}))

    def posted(self, day: date) -> bool:
        return self.receipts.read(self._drive_path(self._path(day, ".posted"))) is not None

    def mark_posted(self, day: date, outcome: str) -> None:
        self.store.put(self._path(day, ".posted"), _json({"day": day.isoformat(), "slack": outcome}))


def _json(body: dict) -> bytes:
    return (json.dumps(body, sort_keys=True, indent=1) + "\n").encode()
