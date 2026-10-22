"""A dated NSE file from a second host when the first is unreachable (story A9c, OSS1 part b): `archives.nseindia.com`
serves the same files byte for byte on another Akamai edge. The second host is asked only when the first raised
`RawSourceUnavailable`, never on a refusal or a cooling-off (the host refused us; asking another edge is no way
around that) and never when the first said "not published" (None stays None). Write times always come from the first
host: they are point-in-time evidence, and equal bytes do not prove equal write times. Every file the second host
serves is logged with its SHA-256 (the manifest row keeps the primary URL, A10's key)."""

from __future__ import annotations

import csv
import hashlib
import io
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from .raw_source import (
    NseArchiveSource,
    PublishedFile,
    RawFileRefused,
    RawFileSource,
    RawSourceCoolingOff,
    RawSourceUnavailable,
)

BOTH_FAILED = "{first}; second host {host}: {second}"
PROVENANCE_FIELDS = ("path", "sha256", "size_bytes", "url", "fetched_at")


class ProvenanceLog(ABC):
    @abstractmethod
    def record(self, source: NseArchiveSource, path: str, data: bytes) -> None:
        """One row for a file the second host served."""


class CsvProvenanceLog(ProvenanceLog):
    """`<folder>/<dataset>.csv`, append-only, inside the manifests folder so the librarian's commit carries it."""

    def __init__(self, folder: Path, clock: Callable[[], datetime] = lambda: datetime.now(UTC)):
        self.folder, self.clock = Path(folder), clock

    def record(self, source: NseArchiveSource, path: str, data: bytes) -> None:
        file = self.folder / f"{source.dataset.rsplit('/', 1)[-1]}.csv"
        file.parent.mkdir(parents=True, exist_ok=True)
        new = not file.is_file()
        row = (path, hashlib.sha256(data).hexdigest(), len(data), source.requested_url(path), self.clock().isoformat())
        out = io.StringIO()
        writer = csv.writer(out, lineterminator="\n")
        if new:
            writer.writerow(PROVENANCE_FIELDS)
        writer.writerow(row)
        with file.open("a", encoding="utf-8") as handle:
            handle.write(out.getvalue())


class FallbackSource(RawFileSource):
    def __init__(self, primary: NseArchiveSource, secondary: NseArchiveSource, log: ProvenanceLog):
        self.primary, self.secondary, self.log = primary, secondary, log
        self.name, self.dataset = primary.name, primary.dataset
        self.first_day, self.last_day = primary.first_day, primary.last_day

    def __getattr__(self, name: str):
        """The dataset's naming (`path_for`, `filename_for`, `url_for`, ...) is the primary's."""
        return getattr(self.primary, name)

    def fetch(self, path: str) -> bytes | None:
        try:
            return self.primary.fetch(path)
        except (RawFileRefused, RawSourceCoolingOff):
            raise
        except RawSourceUnavailable as first:
            data = self._second(path, first, self.secondary.fetch)
        if data is not None:
            self.log.record(self.secondary, path, data)
        return data

    def fetch_published(self, path: str) -> PublishedFile | None:
        """The second host's copy carries no write time: only the first host's dates are evidence."""
        try:
            return self.primary.fetch_published(path)
        except (RawFileRefused, RawSourceCoolingOff):
            raise
        except RawSourceUnavailable as first:
            data = self._second(path, first, self.secondary.fetch)
        if data is None:
            return None
        self.log.record(self.secondary, path, data)
        return PublishedFile(data, None)

    def last_written(self, path: str) -> datetime | None:
        return self.primary.last_written(path)

    def _second(self, path: str, first: RawSourceUnavailable, fetch: Callable[[str], bytes | None]) -> bytes | None:
        try:
            return fetch(path)
        except RawSourceUnavailable as second:
            message = BOTH_FAILED.format(first=first, host=self.secondary.host, second=second)
            raise RawSourceUnavailable(message, second.status, first.tries + second.tries) from second
