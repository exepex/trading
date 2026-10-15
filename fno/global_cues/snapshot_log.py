"""The log of every archived copy of a cue's files (story A17): one CSV per cue in the repository, one row per copy,
append-only, written right after Drive accepted the copy. It is the cue's manifest: the copy's path, the exact
request, its SHA-256 and size, and when it was fetched."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

FIELDS = ("fetched_at", "path", "url", "form", "sha256", "size_bytes")


@dataclass(frozen=True)
class SnapshotRow:
    fetched_at: datetime
    path: str
    url: str
    form: tuple[tuple[str, str], ...]
    sha256: str
    size_bytes: int

    def cells(self) -> tuple:
        form = "&".join(f"{k}={v}" for k, v in self.form)
        return (self.fetched_at.isoformat(), self.path, self.url, form, self.sha256, self.size_bytes)


class SnapshotLog:
    def __init__(self, folder: Path):
        self.folder = Path(folder)

    def path_for(self, cue: str) -> Path:
        return self.folder / f"{cue}.csv"

    def append(self, cue: str, row: SnapshotRow) -> None:
        file = self.path_for(cue)
        new = not file.is_file()
        self.folder.mkdir(parents=True, exist_ok=True)
        with file.open("a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, lineterminator="\n")
            if new:
                writer.writerow(FIELDS)
            writer.writerow(row.cells())

    def paths_by_sha256(self, cue: str) -> dict[str, str]:
        """SHA-256 -> the archived copy's path (the first copy with those bytes)."""
        file = self.path_for(cue)
        rows = csv.DictReader(file.read_text(encoding="utf-8").splitlines()) if file.is_file() else []
        found: dict[str, str] = {}
        for row in rows:
            found.setdefault(row["sha256"], row["path"])
        return found
