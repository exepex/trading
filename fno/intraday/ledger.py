"""The per-session slot ledger in the repository (story A16): one row per due mark, written once, holding only times,
counts, statuses and SHA-256 values (never a price: raw quotes stay in Drive, design 4.4). A mark nobody took is a
`missed` row, never filled later."""

from __future__ import annotations

import csv
import io
from datetime import date, datetime
from pathlib import Path

from .clock import ClockReading
from .document import SnapshotDocument, utc_text
from .slots import label
from .status import MISSED, SlotVerdict

FIELDS = (
    "session", "mark", "mark_ist", "status", "failures", "request_sent_at", "response_received_at",
    "index_source_time", "lateness_seconds", "index_age_seconds", "expected_contracts", "recorded_contracts",
    "two_sided_contracts", "clock_status", "clock_skew_seconds", "raw_path", "raw_sha256", "source", "first_seen_at",
    "alert",
)  # fmt: skip
NOT_TAKEN = "not_taken"
FILE_NAME = "slots/{day:%Y}/{day:%m}/nifty_{day:%Y%m%d}.csv"


class SlotLedger:
    def __init__(self, folder: Path):
        self.folder = Path(folder)

    def path(self, day: date) -> Path:
        return self.folder / FILE_NAME.format(day=day)

    def rows(self, day: date) -> list[dict]:
        file = self.path(day)
        return list(csv.DictReader(io.StringIO(file.read_text(encoding="utf-8")))) if file.is_file() else []

    def append(self, day: date, rows: list[dict]) -> None:
        """Adds rows for marks that have none; a second row for a mark is refused (rows are never rewritten)."""
        if not rows:
            return
        taken = {row["mark"] for row in self.rows(day)}
        if clash := sorted(taken & {row["mark"] for row in rows}):
            raise ValueError(f"ledger already has rows for {clash}: rows are written once")
        file = self.path(day)
        file.parent.mkdir(parents=True, exist_ok=True)
        new = not file.is_file()
        with file.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
            if new:
                writer.writeheader()
            writer.writerows(rows)


def taken_row(doc: SnapshotDocument, verdict: SlotVerdict, raw_path: str, raw_sha256: str,
              clock: ClockReading | None) -> dict:  # fmt: skip
    """The row of a stored snapshot."""
    received, source_time = doc.index.response_received_at, doc.index_source_time
    return {
        **_mark_fields(doc.session, doc.mark, doc.source), "status": verdict.status,
        "failures": ";".join(verdict.failures), "request_sent_at": utc_text(doc.index.request_sent_at),
        "response_received_at": utc_text(received), "index_source_time": utc_text(source_time),
        "lateness_seconds": _seconds(received, doc.mark), "index_age_seconds": _seconds(received, source_time),
        "expected_contracts": doc.expected_contracts, "recorded_contracts": doc.recorded_contracts,
        "two_sided_contracts": doc.two_sided_contracts, "clock_status": clock.status if clock else "",
        "clock_skew_seconds": _number(clock.worst if clock else None), "raw_path": raw_path, "raw_sha256": raw_sha256,
        "first_seen_at": utc_text(doc.finished_at), "alert": "",
    }  # fmt: skip


def missed_row(day: date, mark: datetime, source: str, noticed_at: datetime) -> dict:
    """The row of a mark whose window passed with no snapshot stored."""
    row = dict.fromkeys(FIELDS, "")
    row.update(_mark_fields(day, mark, source), status=MISSED, failures=NOT_TAKEN, first_seen_at=utc_text(noticed_at))
    return row


def _mark_fields(day: date, mark: datetime, source: str) -> dict:
    return {"session": day.isoformat(), "mark": utc_text(mark), "mark_ist": label(mark), "source": source}


def _seconds(later: datetime | None, earlier: datetime | None) -> str:
    return _number((later - earlier).total_seconds()) if later and earlier else ""


def _number(value: float | None) -> str:
    return "" if value is None else f"{value:.1f}"
