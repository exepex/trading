"""The study's raw inputs: copies Drive files to a local cache, each checked against its SHA-256 manifest row.

Copying reads no content: a file is bytes and a hash until the analysis parses it (PROTOCOL.md section 11 allows file
counts before the run). A file whose hash differs from its manifest row is refused, never used.
"""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]
MANIFESTS = REPOSITORY / "research" / "data" / "manifests"
FETCH_THREADS = 8


@dataclass(frozen=True)
class DatasetFiles:
    """One dated dataset: its manifest, the Drive path and original name of a day's file."""

    name: str  # manifest name, e.g. "fo-bhavcopy"
    path_for: Callable[[date], str]
    filename_for: Callable[[date], str]
    first: date
    last: date | None = None


class HashMismatch(RuntimeError):
    """A file's SHA-256 differs from its manifest row: never used."""


def manifest_rows(name: str, folder: Path = MANIFESTS) -> dict[date, str]:
    """Day -> SHA-256 of every archived file (status 200) of one dataset."""
    with (folder / f"{name}.csv").open(newline="") as handle:
        return {date.fromisoformat(r["date"]): r["sha256"] for r in csv.DictReader(handle) if r["status"] == "200"}


def cached_file(cache: Path, dataset: DatasetFiles, day: date) -> Path:
    return cache / dataset.name / f"{day.isoformat()}_{dataset.filename_for(day)}"


def checked(data: bytes, expected: str, label: str) -> bytes:
    if hashlib.sha256(data).hexdigest() != expected:
        raise HashMismatch(f"{label}: SHA-256 differs from its manifest row")
    return data


class InputCache:
    """Local copies of a dataset's files; `get_bytes(path)` reads one file from Drive (or another store)."""

    def __init__(self, cache: Path, get_bytes: Callable[[str], bytes | None], manifests: Path = MANIFESTS):
        self.cache, self.get_bytes, self.manifests = cache, get_bytes, manifests

    def days(self, dataset: DatasetFiles) -> list[date]:
        rows = manifest_rows(dataset.name, self.manifests)
        last = dataset.last or date.max
        return sorted(d for d in rows if dataset.first <= d <= last)

    def fetch(self, dataset: DatasetFiles, log=print) -> dict[str, int]:
        """Copies every manifest day not yet cached; returns counts (cached, copied, missing)."""
        rows = manifest_rows(dataset.name, self.manifests)
        todo = [d for d in self.days(dataset) if not cached_file(self.cache, dataset, d).exists()]
        counts = {"cached": len(self.days(dataset)) - len(todo), "copied": 0, "missing": 0}

        def copy(day: date) -> bool:
            data = self.get_bytes(dataset.path_for(day))
            if data is None:
                return False
            target = cached_file(self.cache, dataset, day)
            target.parent.mkdir(parents=True, exist_ok=True)
            partial = target.with_suffix(target.suffix + ".part")
            partial.write_bytes(checked(data, rows[day], target.name))
            partial.replace(target)
            return True

        with ThreadPoolExecutor(FETCH_THREADS) as pool:
            for done in pool.map(copy, todo):
                counts["copied" if done else "missing"] += 1
        log(f"{dataset.name}: {counts}")
        return counts

    def read(self, dataset: DatasetFiles, day: date) -> tuple[str, bytes] | None:
        """(original file name, bytes) of a cached day, checked again against the manifest; None if not cached."""
        target = cached_file(self.cache, dataset, day)
        if not target.exists():
            return None
        expected = manifest_rows(dataset.name, self.manifests).get(day)
        if expected is None:
            raise HashMismatch(f"{target.name}: no manifest row")
        return dataset.filename_for(day), checked(target.read_bytes(), expected, target.name)
