"""Raw snapshots kept by A11's revision rule (story A16): the first bytes saved at a path stay the raw file; different
bytes later offered for the same path (two overlapping runs taking one mark) are never written over it: they go to the
`revisions` area under A11's layout (`<raw path>/<found_at>_<sha256><suffixes>`) with an index record in its own file
(`revisions/<file stem>_<sha256 first 16>.csv`, so two runs never write the same index file). Readers get the first
version, which is what was known first (point in time). `put_first` tells the caller whether its bytes are that first
version: only that run writes the mark's ledger row (story A16, "Two checkouts, one ledger")."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import datetime
from pathlib import Path, PurePosixPath

from ..models import now_ist
from ..storage.raw_store import RawFileConflict, RawFileStore
from .document import utc_text
from .row_files import read_rows, write_row

INDEX_FIELDS = ("path", "sha256", "size_bytes", "found_at", "revision_path")
REVISION_NAME = "{at:%Y%m%dT%H%M%S%z}_{sha256}{suffix}"
INDEX_NAME = "{stem}_{sha256:.16}.csv"


class FirstVersionStore(RawFileStore):
    def __init__(self, raw: RawFileStore, revisions: RawFileStore, index_folder: Path,
                 clock: Callable[[], datetime] = now_ist):  # fmt: skip
        self.raw, self.revisions, self.index_folder, self.clock = raw, revisions, Path(index_folder), clock
        self.name = raw.name

    def get(self, path: str) -> bytes | None:
        return self.raw.get(path)

    def put(self, path: str, data: bytes) -> None:
        self.put_first(path, data)

    def put_first(self, path: str, data: bytes) -> bool:
        """Saves the bytes; True when they are the path's first version (saved now or already identical), False when
        another version was there first and these went to the revisions area."""
        try:
            self.raw.put(path, data)
        except RawFileConflict:
            self._save_revision(path, data)
            return False
        return True

    def rows(self) -> list[dict]:
        return read_rows(self.index_folder, "*.csv")

    def _save_revision(self, path: str, data: bytes) -> None:
        sha256, found_at = hashlib.sha256(data).hexdigest(), self.clock()
        stem = PurePosixPath(path).name.split(".")[0]
        index_file = self.index_folder / INDEX_NAME.format(stem=stem, sha256=sha256)
        if index_file.exists():
            return  # this version is already archived
        suffix = "".join(PurePosixPath(path).suffixes)
        revision_path = f"{path}/{REVISION_NAME.format(at=found_at, sha256=sha256, suffix=suffix)}"
        self.revisions.put(revision_path, data)  # bytes first: an index record always has its file
        write_row(index_file, INDEX_FIELDS, dict(zip(INDEX_FIELDS, [path, sha256, len(data), utc_text(found_at),
                                                                    revision_path])))  # fmt: skip
