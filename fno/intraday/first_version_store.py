"""Raw snapshots kept by A11's revision rule (story A16): the first bytes saved at a path stay the raw file; different
bytes later offered for the same path (two hosts taking one mark) are never written over it: they go to the
`revisions` area under A11's layout (`<raw path>/<found_at>_<sha256><suffixes>`) with one row in an append-only index.
Readers get the first version, which is what was known first (point in time)."""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Callable
from datetime import datetime
from pathlib import Path, PurePosixPath

from ..models import now_ist
from ..storage.raw_store import RawFileConflict, RawFileStore
from .document import utc_text

INDEX_FIELDS = ("path", "sha256", "size_bytes", "found_at", "revision_path")
REVISION_NAME = "{at:%Y%m%dT%H%M%S%z}_{sha256}{suffix}"


class FirstVersionStore(RawFileStore):
    def __init__(self, raw: RawFileStore, revisions: RawFileStore, index_file: Path,
                 clock: Callable[[], datetime] = now_ist):  # fmt: skip
        self.raw, self.revisions, self.index_file, self.clock = raw, revisions, Path(index_file), clock
        self.name = raw.name
        self.revised: list[str] = []  # revision paths saved by this store since it was made

    def get(self, path: str) -> bytes | None:
        return self.raw.get(path)

    def put(self, path: str, data: bytes) -> None:
        try:
            self.raw.put(path, data)
        except RawFileConflict:
            self._save_revision(path, data)

    def _save_revision(self, path: str, data: bytes) -> None:
        sha256, found_at = hashlib.sha256(data).hexdigest(), self.clock()
        if sha256 in {row["sha256"] for row in self.rows() if row["path"] == path}:
            return  # this version is already archived
        suffix = "".join(PurePosixPath(path).suffixes)
        revision_path = f"{path}/{REVISION_NAME.format(at=found_at, sha256=sha256, suffix=suffix)}"
        self.revisions.put(revision_path, data)  # bytes first: an index row always has its file
        self._append([path, sha256, len(data), utc_text(found_at), revision_path])
        self.revised.append(revision_path)

    def rows(self) -> list[dict]:
        if not self.index_file.is_file():
            return []
        return list(csv.DictReader(self.index_file.read_text(encoding="utf-8").splitlines()))

    def _append(self, row: list) -> None:
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        new = not self.index_file.is_file()
        with self.index_file.open("a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, lineterminator="\n")
            if new:
                writer.writerow(INDEX_FIELDS)
            writer.writerow(row)
