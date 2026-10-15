"""One realised-variance record per session in the repository (story A16), one file each
(`rv/<YYYY>/nifty_rv_<YYYYMMDD>.csv`), written once: the same inputs again change nothing; different inputs for a
session already written are refused (a figure, once first seen, never changes)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from .row_files import read_rows, write_row

FIELDS = (
    "session", "status", "rv_session", "rv_intraday", "rv_overnight", "vol_pct", "void_reason", "good_slots",
    "due_slots", "basis_counts", "measure", "method", "source", "as_of", "first_seen_at", "inputs_sha256",
)  # fmt: skip
ROOT = "rv/"  # everything the table writes is under this folder
FILE_NAME = ROOT + "{day:%Y}/nifty_rv_{day:%Y%m%d}.csv"
PATTERN = ROOT + "*/nifty_rv_*.csv"
SAME_INPUTS = ("method", "inputs_sha256")
WRITTEN, ALREADY = "written", "already written"


class RvConflict(RuntimeError):
    """A session already has a row computed from different inputs; nothing was changed."""


class RvTable:
    def __init__(self, folder: Path):
        self.folder = Path(folder)

    def path(self, day: date) -> Path:
        return self.folder / FILE_NAME.format(day=day)

    def rows(self) -> list[dict]:
        return read_rows(self.folder, PATTERN)

    def write_once(self, row: dict) -> str:
        path = self.path(date.fromisoformat(row["session"]))
        found = read_rows(path.parent, path.name)
        if found:
            if all(found[0][k] == str(row[k]) for k in SAME_INPUTS):
                return ALREADY
            raise RvConflict(f"{row['session']}: already written from other inputs; rows are never changed")
        write_row(path, FIELDS, row)
        return WRITTEN
