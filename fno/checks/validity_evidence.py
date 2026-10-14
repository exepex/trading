"""C4's evidence (story C4): the raw A4 quote snapshot a decision was made on, read again from the store and accepted
only if it is the committed capture (C3's `CaptureRecord`: both files' SHA-256 equal), of the decision's day, started
before the decision cutoff. Rows are parsed here from the raw CSV, not through the desk's own snapshot reader."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import date, datetime

from ..quotes.recorder import QuoteSnapshotRecorder
from ..storage.raw_store import RawFileStore
from .data_checks import CaptureRecord

Key = tuple[str, float, str]  # (expiry ISO, strike, "CE" or "PE")


@dataclass(frozen=True)
class QuoteRow:
    bid: float | None
    ask: float | None
    received_at: datetime | None

    @property
    def mid(self) -> float | None:
        return None if self.bid is None or self.ask is None else (self.bid + self.ask) / 2


@dataclass(frozen=True)
class Evidence:
    snapshot_id: str
    started_at: datetime
    monthly_expiries: tuple[str, ...]  # the latest listed expiry of each calendar month in the snapshot
    rows: dict[Key, QuoteRow]


def _time(text: str) -> datetime | None:
    try:
        return datetime.fromisoformat(text) if text else None
    except ValueError:
        return None


def _number(text: str) -> float | None:
    return float(text) if text else None


def _hash_problem(name: str, data: bytes, expected: str) -> list[str]:
    actual = hashlib.sha256(data).hexdigest()
    return [] if actual == expected else [f"{name} SHA-256 {actual[:12]} differs from the record's {expected[:12]}"]


def _key(row: dict) -> Key:
    return row["expiry"], float(row["strike"]), row["type"]


def monthly_expiries(expiries) -> tuple[str, ...]:
    """NIFTY's monthly expiry is the last of its month: the latest listed expiry in each calendar month."""
    latest: dict[str, str] = {}
    for expiry in expiries:
        latest[expiry[:7]] = max(latest.get(expiry[:7], expiry), expiry)
    return tuple(sorted(latest.values()))


def _row(row: dict) -> QuoteRow:
    return QuoteRow(_number(row["bid"]), _number(row["ask"]), _time(row["response_received_at"]))


class EvidenceReader:
    def __init__(self, store: RawFileStore, dataset: str):
        self.store, self.dataset = store, dataset

    def read(self, day: date, record: CaptureRecord | None) -> tuple[Evidence | None, list[str]]:
        """(the evidence, []) or (None, why it cannot be trusted)."""
        if record is None:
            return None, ["no committed capture record names the decision's snapshot"]
        csv_bytes, meta_bytes = (
            self.store.get(QuoteSnapshotRecorder.path(day, f"{record.snapshot_id}{suffix}", self.dataset))
            for suffix in (".csv", ".meta.json")
        )
        if not csv_bytes or not meta_bytes:
            return None, [f"snapshot {record.snapshot_id} of {day} is missing from the store"]
        problems = _hash_problem("quote file", csv_bytes, record.csv_sha256)
        problems += _hash_problem("meta file", meta_bytes, record.meta_sha256)
        if problems:
            return None, problems
        meta = json.loads(meta_bytes)
        rows = {_key(r): _row(r) for r in csv.DictReader(io.StringIO(csv_bytes.decode("utf-8")))}
        expiries = monthly_expiries(key[0] for key in rows)
        return Evidence(record.snapshot_id, datetime.fromisoformat(meta["started_at"]), expiries, rows), []
