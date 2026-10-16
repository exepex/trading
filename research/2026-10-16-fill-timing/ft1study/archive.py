"""The contracts' raw candle answers kept in the owner's Drive (PROTOCOL.md section 17), in A16b's pattern: one gzip
JSON document per answer (no time in the gzip header, so the same answer gives the same bytes) under a content-addressed
name, Drive first and then the manifest row (symbol, window, path, SHA-256, size, times; never a price). The analysis
reads only these copies, each checked against its row; a local cache keyed by SHA-256 saves reading Drive twice."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from datetime import date
from pathlib import Path

from fno.storage.raw_store import RawFileStore

from .candles import ContractAnswer

PATH = "groww/options/nifty-candles-15m/{expiry:%Y}/{expiry}/{symbol}_{start:%Y%m%d}_{end:%Y%m%d}_{sha:.16}.json.gz"
MANIFEST_NAME = "nifty-options-15m.csv"
FIELDS = ("symbol", "expiry", "start", "end", "path", "sha256", "size", "requested_at", "fetched_at")


class CopyDamaged(ValueError):
    """A copy is missing from Drive or its bytes differ from its manifest row."""


class ContractArchive:
    def __init__(self, store: RawFileStore, manifest: Path, cache: Path | None = None):
        self.store, self.manifest, self.cache = store, Path(manifest), cache
        self._rows: list[dict[str, str]] | None = None

    def save(self, expiry: date, answer: ContractAnswer) -> str:
        data = gzip.compress(answer.raw, mtime=0)
        sha256 = hashlib.sha256(data).hexdigest()
        path = PATH.format(expiry=expiry, symbol=answer.symbol, start=answer.start, end=answer.end, sha=sha256)
        self.store.put(path, data)
        if not any(r["path"] == path for r in self.rows()):
            times = answer.requested_at.isoformat(), answer.received_at.isoformat()
            self._append([answer.symbol, expiry.isoformat(), answer.start.isoformat(), answer.end.isoformat(), path,
                          sha256, len(data), *times])  # fmt: skip
        return path

    def held(self, symbol: str, start: date, end: date) -> bool:
        first, last = start.isoformat(), end.isoformat()
        return any(r["symbol"] == symbol and r["start"] == first and r["end"] == last for r in self.rows())

    def copies(self, symbol: str) -> list[list]:
        """Every copy's candle rows for `symbol`, earliest fetched first."""
        rows = sorted((r for r in self.rows() if r["symbol"] == symbol), key=lambda r: r["fetched_at"])
        return [self.load(r) for r in rows]

    def load(self, row: dict[str, str]) -> list:
        cached = self._cached(row["sha256"])
        data = cached if cached is not None else self.store.get(row["path"])
        if data is None:
            raise CopyDamaged(f"{row['path']}: not in Drive")
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise CopyDamaged(f"{row['path']}: SHA-256 differs from its manifest row")
        if cached is None:
            self._keep(row["sha256"], data)
        return json.loads(gzip.decompress(data))["candles"]

    def rows(self) -> list[dict[str, str]]:
        if self._rows is None:
            text = self.manifest.read_text(encoding="utf-8") if self.manifest.is_file() else ""
            self._rows = list(csv.DictReader(text.splitlines()))
        return self._rows

    def _append(self, values: list) -> None:
        new = not self.manifest.is_file() or not self.manifest.stat().st_size
        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        with self.manifest.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            if new:
                writer.writerow(FIELDS)
            writer.writerow(values)
        self.rows().append(dict(zip(FIELDS, map(str, values), strict=True)))

    def _cached(self, sha256: str) -> bytes | None:
        path = self.cache / f"{sha256}.json.gz" if self.cache else None
        return path.read_bytes() if path and path.is_file() else None

    def _keep(self, sha256: str, data: bytes) -> None:
        if self.cache:
            self.cache.mkdir(parents=True, exist_ok=True)
            (self.cache / f"{sha256}.json.gz").write_bytes(data)
