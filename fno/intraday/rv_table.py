"""One realised-variance row per session in the repository (story A16), written once: the same inputs again change
nothing, different inputs for a session already written are refused (a figure, once first seen, never changes)."""

from __future__ import annotations

import csv
import io
from pathlib import Path

FIELDS = (
    "session", "status", "rv_session", "rv_intraday", "rv_overnight", "vol_pct", "void_reason", "good_marks",
    "due_marks", "measure", "method", "source", "as_of", "first_seen_at", "inputs_sha256",
)  # fmt: skip
FILE_NAME = "rv/nifty_rv.csv"
SAME_INPUTS = ("method", "inputs_sha256")
WRITTEN, ALREADY = "written", "already written"


class RvConflict(RuntimeError):
    """A session already has a row computed from different inputs; nothing was changed."""


class RvTable:
    def __init__(self, folder: Path):
        self.file = Path(folder) / FILE_NAME

    def rows(self) -> list[dict]:
        if not self.file.is_file():
            return []
        return list(csv.DictReader(io.StringIO(self.file.read_text(encoding="utf-8"))))

    def write_once(self, row: dict) -> str:
        found = [r for r in self.rows() if r["session"] == row["session"]]
        if found:
            if all(found[0][k] == str(row[k]) for k in SAME_INPUTS):
                return ALREADY
            raise RvConflict(f"{row['session']}: already written from other inputs; rows are never changed")
        self.file.parent.mkdir(parents=True, exist_ok=True)
        new = not self.file.is_file()
        with self.file.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
            if new:
                writer.writeheader()
            writer.writerow(row)
        return WRITTEN
