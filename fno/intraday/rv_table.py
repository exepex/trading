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
    """A16's table; a subclass with its own file layout and columns keeps every rule (story A16b)."""

    fields, file_name, pattern = FIELDS, FILE_NAME, PATTERN

    def __init__(self, folder: Path):
        self.folder = Path(folder)

    def path(self, day: date) -> Path:
        return self.folder / self.file_name.format(day=day)

    def rows(self) -> list[dict]:
        return read_rows(self.folder, self.pattern)

    def row(self, day: date) -> dict | None:
        path = self.path(day)
        found = read_rows(path.parent, path.name)
        return found[0] if found else None

    def write_once(self, row: dict) -> str:
        day = date.fromisoformat(row["session"])
        held = self.row(day)
        if held:
            if all(held[k] == str(row[k]) for k in SAME_INPUTS):
                return ALREADY
            raise RvConflict(f"{row['session']}: already written from other inputs; rows are never changed")
        write_row(self.path(day), self.fields, row)
        return WRITTEN
