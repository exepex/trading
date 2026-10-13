"""Where the NIFTY option-chain panel (story A3) is kept: the `PanelSink` interface and its folder of yearly
`options_<year>.csv.gz` files plus `manifest.json`.

Deterministic: rows arrive sorted by date, expiry, strike and type; the column order is fixed; gzip is written with
no file name and a zero timestamp; the manifest is sorted JSON with no build time in it. So the same raw files give
byte-identical outputs. Files are written under temporary names and swapped in only when the whole build succeeded.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from pathlib import Path

PANEL_COLUMNS = (
    "date", "expiry", "strike", "type", "close", "settle", "volume", "open_interest", "underlying", "vix",
    "source_format",
)  # fmt: skip
OPTIONS_FILE = "options_{year}.csv.gz"
OPTIONS_GLOB = "options_*.csv.gz"
MANIFEST_FILE = "manifest.json"
PART_SUFFIX = ".part"
GZIP_LEVEL = 9


def file_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class PanelDay:
    day: date
    entry: dict  # the day's manifest entry: session kind, status, source files and their SHA-256, row count
    rows: list[tuple[str, ...]]  # in PANEL_COLUMNS order, sorted


@dataclass(frozen=True)
class Panel:
    manifest: dict


class PanelSink(ABC):
    @abstractmethod
    def add(self, panel_day: PanelDay) -> None:
        """Takes the days in date order."""

    @abstractmethod
    def finish(self, header: dict) -> Panel:
        """Makes the build final; the manifest is `header` plus the days and the output files."""

    @abstractmethod
    def discard(self) -> None:
        """Drops everything added; the previous panel stays as it was."""


class CsvGzPanelFolder(PanelSink):
    def __init__(self, folder: Path):
        self.folder = folder
        self.days: dict[str, dict] = {}
        self._year: int | None = None
        self._raw = self._text = self._writer = None
        self._parts: list[Path] = []

    def add(self, panel_day: PanelDay) -> None:
        self.days[panel_day.day.isoformat()] = panel_day.entry
        if not panel_day.rows:
            return
        if panel_day.day.year != self._year:
            self._open(panel_day.day.year)
        self._writer.writerows(panel_day.rows)

    def _open(self, year: int) -> None:
        self._close()
        self.folder.mkdir(parents=True, exist_ok=True)
        part = self.folder / (OPTIONS_FILE.format(year=year) + PART_SUFFIX)
        self._parts.append(part)
        self._raw = part.open("wb")
        gz = gzip.GzipFile(filename="", mode="wb", fileobj=self._raw, compresslevel=GZIP_LEVEL, mtime=0)
        self._text = io.TextIOWrapper(gz, encoding="utf-8", newline="")
        self._writer = csv.writer(self._text, lineterminator="\n")
        self._writer.writerow(PANEL_COLUMNS)
        self._year = year

    def _close(self) -> None:
        if self._text is not None:
            self._text.close()  # closes the gzip stream, which writes its trailer
            self._raw.close()
        self._raw = self._text = self._writer = None

    def finish(self, header: dict) -> Panel:
        self._close()
        files = {}
        for part in self._parts:
            final = part.with_name(part.name.removesuffix(PART_SUFFIX))
            data = part.read_bytes()
            text = gzip.decompress(data)  # its SHA-256 checks the content whatever zlib version compressed it
            files[final.name] = {
                "sha256": file_sha256(data),
                "csv_sha256": file_sha256(text),
                "rows": text.count(b"\n") - 1,
            }
        manifest = {**header, "files": files, "days": self.days}
        for old in self.folder.glob(OPTIONS_GLOB):
            if old.name not in files:
                old.unlink()  # a year outside this build would not match its manifest
        for part in self._parts:
            part.replace(part.with_name(part.name.removesuffix(PART_SUFFIX)))
        (self.folder / MANIFEST_FILE).write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", "utf-8")
        return Panel(manifest)

    def discard(self) -> None:
        self._close()
        for part in self._parts:
            part.unlink(missing_ok=True)
        self._parts, self.days = [], {}
