"""The 15:45 report's records in O9's data store (stories FL1-1 and FL1-1c): the report (text, alerts, what it
covered, and the picture and details file as base64, so a rerun posts exactly what was made), its posted marker and
its alerts' marker, each a write-once JSON file in Drive's data area with its receipt under
`receipts/`. A report is read back verified against its receipt's SHA-256 (the Drive cache's check, for one file; the
cache syncs whole folders): a missing or damaged copy stops the run, never a silent rebuild."""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import date

from ..storage.data_store import DataStore
from ..storage.receipts import ReceiptFolder
from .constants import REPORT_AREA
from .delivery import Attachment
from .lab_close import ReportRecords
from .written import WrittenReport

UNREADABLE = "the written 15:45 report of {day} cannot be read back verified: {problems}"


class DriveReportRecords(ReportRecords):
    def __init__(self, store: DataStore, receipts: ReceiptFolder):
        self.store, self.receipts = store, receipts

    @staticmethod
    def _path(day: date, suffix: str = "") -> str:
        return f"{REPORT_AREA}/{day:%Y}/{day.isoformat()}{suffix}.json"

    def _drive_path(self, path: str) -> str:
        return f"{self.store.area}/{path}"

    def report(self, day: date) -> WrittenReport | None:
        drive_path = self._drive_path(self._path(day))
        receipt = self.receipts.read(drive_path)
        if receipt is None:
            return None
        data = self.store.drive.get(drive_path)
        if data is None or hashlib.sha256(data).hexdigest() != receipt.sha256:
            raise RuntimeError(UNREADABLE.format(day=day, problems="missing" if data is None else "damaged"))
        body = json.loads(data)
        files = tuple(Attachment(f["name"], base64.b64decode(f["data"]), f["title"]) for f in body.get("files", []))
        return WrittenReport(body["text"], tuple(body["alerts"]), tuple(body["checked"]), tuple(body["matched"]),
                             files)  # fmt: skip

    def write_report(self, day: date, report: WrittenReport) -> None:
        files = [{"name": f.name, "title": f.title, "data": base64.b64encode(f.data).decode("ascii")}
                 for f in report.attachments]  # fmt: skip
        body = {"day": day.isoformat(), "text": report.text, "alerts": list(report.alerts),
                "checked": list(report.checked), "matched": list(report.matched), "files": files}  # fmt: skip
        self.store.put(self._path(day), _json(body))

    def posted(self, day: date) -> bool:
        return self.receipts.read(self._drive_path(self._path(day, ".posted"))) is not None

    def mark_posted(self, day: date, outcome: str) -> None:
        self.store.put(self._path(day, ".posted"), _json({"day": day.isoformat(), "slack": outcome}))

    def alerted(self, day: date) -> bool:
        return self.receipts.read(self._drive_path(self._path(day, ".alerted"))) is not None

    def mark_alerted(self, day: date, outcomes: list[str]) -> None:
        self.store.put(self._path(day, ".alerted"), _json({"day": day.isoformat(), "outcomes": list(outcomes)}))


def _json(body: dict) -> bytes:
    return (json.dumps(body, sort_keys=True, indent=1) + "\n").encode()
