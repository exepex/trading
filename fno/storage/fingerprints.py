"""SHA-256 manifests of a dataset's archived files (story A9): read every file a store holds, read-only, and write the
fingerprints in the laptop tool's manifest layout, so the coverage check can prove later that no file changed.

A manifest made here records what the archive holds (status 200 rows only); it says nothing about days without a file.
Comparing a sample with the source's live bytes tells whether the publisher has rewritten a file since: a difference
is reported as a rewrite, never "fixed" in the archive (raw files never change).
"""

from __future__ import annotations

import csv
import hashlib
import io
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..research_data.calendar import SessionCalendar
from .coverage import DEFAULT_WORKERS, archive_range, days_between
from .raw_source import NseArchiveSource
from .raw_store import RawFileStore

MANIFEST_FIELDS = ("date", "url", "status", "sha256", "size_bytes")  # read by coverage.read_fingerprints
PUBLISHED = "200"


@dataclass(frozen=True)
class Fingerprint:
    day: date
    url: str
    sha256: str
    size_bytes: int


def fingerprint_store(
    store: RawFileStore,
    source: type[NseArchiveSource],
    calendar: SessionCalendar,
    start: date,
    end: date,
    workers: int = DEFAULT_WORKERS,
) -> list[Fingerprint]:
    """The fingerprint of every file the store holds for the source's sessions from start to end, in day order."""
    days = [day for day in days_between(*archive_range(source, start, end)) if calendar.is_session(day)]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        files = list(pool.map(lambda day: store.get(source.path_for(day)), days))
    return [
        Fingerprint(day, source.url_for(source.path_for(day)), hashlib.sha256(data).hexdigest(), len(data))
        for day, data in zip(days, files)
        if data is not None
    ]


def manifest_text(fingerprints: list[Fingerprint]) -> str:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(MANIFEST_FIELDS)
    writer.writerows((f.day.isoformat(), f.url, PUBLISHED, f.sha256, f.size_bytes) for f in fingerprints)
    return out.getvalue()


def write_manifest(path: Path, fingerprints: list[Fingerprint]) -> None:
    path.write_text(manifest_text(fingerprints), encoding="utf-8")


def compare_with_source(source: NseArchiveSource, fingerprints: list[Fingerprint]) -> list[str]:
    """One line per file: whether the source's live bytes still equal the archived fingerprint."""
    lines = []
    for f in fingerprints:
        live = source.fetch(source.path_for(f.day))
        if live is None:
            lines.append(f"{f.day} {f.url}: the source no longer serves it (archive copy kept)")
        elif hashlib.sha256(live).hexdigest() == f.sha256:
            lines.append(f"{f.day} {f.url}: identical")
        else:
            lines.append(f"{f.day} {f.url}: NSE REWRITE: live bytes differ from the archived file (archive kept)")
    return lines
