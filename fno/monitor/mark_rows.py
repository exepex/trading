"""The monitor's public record (story LM1): one row per mark handled, counts and times only, never a position or a
price, in `research/data/intraday/monitor/<YYYY>/<MM>/<DD>/marks.csv` (inside A16's folder, so the rows go up in
A16's own commit). The row is the one-handling marker: a mark whose row exists, whatever its status, is never handled
again, so overlapping recorder runs, or a rerun after Drive recovers, never send a mark's alerts twice."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from ..intraday.document import utc_text
from ..models import IST

FILE_NAME = "{day:%Y}/{day:%m}/{day:%d}/marks.csv"
COLUMNS = ("session", "mark", "mark_ist", "finished_at", "status", "checked", "positions", "alerts_sent",
           "alerts_failed", "held", "record", "previous_close_known", "failure")  # fmt: skip
RECORD_OK, RECORD_FAILED, RECORD_NONE = "ok", "alert_record_failed", "none"


@dataclass(frozen=True)
class MarkRow:
    session: date
    mark: datetime
    finished_at: datetime
    status: str  # A16's slot status of the mark
    checked: bool  # the checks ran on it (usable mark, positions open)
    positions: int
    alerts_sent: int = 0
    alerts_failed: int = 0
    held: int = 0
    record: str = RECORD_NONE
    previous_close_known: bool = True
    failure: str = ""  # the monitor's own failure, by class name only

    def as_csv(self) -> dict[str, str]:
        return {
            "session": self.session.isoformat(), "mark": utc_text(self.mark),
            "mark_ist": f"{self.mark.astimezone(IST):%H:%M}", "finished_at": utc_text(self.finished_at),
            "status": self.status, "checked": str(self.checked), "positions": str(self.positions),
            "alerts_sent": str(self.alerts_sent), "alerts_failed": str(self.alerts_failed), "held": str(self.held),
            "record": self.record, "previous_close_known": str(self.previous_close_known), "failure": self.failure,
        }  # fmt: skip


class MarkRows:
    def __init__(self, folder: Path):
        self.folder = Path(folder)

    def path(self, day: date) -> Path:
        return self.folder / FILE_NAME.format(day=day)

    def rows(self, day: date) -> list[dict[str, str]]:
        path = self.path(day)
        return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8")))) if path.is_file() else []

    def handled(self, day: date, mark: datetime) -> bool:
        return any(r["mark"] == utc_text(mark) for r in self.rows(day))

    def append(self, row: MarkRow) -> None:
        path = self.path(row.session)
        new = not path.is_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
            if new:
                writer.writeheader()
            writer.writerow(row.as_csv())
