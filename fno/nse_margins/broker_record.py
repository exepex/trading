"""A14c part 2's record (story O9): every run writes one write-once file in Drive's data area,
`data/margins/broker_checks/<as_of>/<run time IST>.csv`, one row per basket; its SHA-256 receipt is what GitHub keeps,
committed by O1's step through `receipt_pathspecs()` (never the whole shared `receipts/` tree). Nothing is appended in
GitHub. The day's earlier records, read back through the verified Drive cache, tell which baskets are already done."""

from __future__ import annotations

import csv
import io
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, datetime

from ..storage.data_store import DataStore
from ..storage.drive_cache import DriveCache
from .broker_compare import MISMATCH, OK

FOLDER = "margins/broker_checks"  # under O9's `data` area
RECORD_PATH = FOLDER + "/{as_of}/{run:%H%M%S}.csv"
RECEIPTS = "receipts/data/" + FOLDER + "/"
COLUMNS = ("checked_at", "as_of", "structure", "width", "span_broker_rs", "span_expected_rs", "exposure_broker_rs",
           "exposure_expected_rs", "status", "detail")  # fmt: skip
DONE = (OK, MISMATCH)  # a result that is never asked again; an `error` is retried by a same-day rerun only
UNREADABLE = "the day's earlier records cannot be read back from Drive: {problems}"


class RecordProblem(RuntimeError):
    """The day's record could not be read or written (the check exits 1)."""


def receipt_pathspecs() -> tuple[str, ...]:
    """What O1's `margin_check` step commits: this check's receipts only."""
    return (RECEIPTS,)


@dataclass(frozen=True)
class BrokerResult:
    checked_at: datetime
    as_of: date
    structure: str
    width: float
    span_broker: float | None
    span_expected: float | None
    exposure_broker: float | None
    exposure_expected: float | None
    status: str
    detail: str

    def as_row(self) -> tuple[str, ...]:
        figures = (self.span_broker, self.span_expected, self.exposure_broker, self.exposure_expected)
        return (self.checked_at.isoformat(timespec="seconds"), self.as_of.isoformat(), self.structure,
                f"{self.width:g}", *("" if f is None else f"{f:.2f}" for f in figures), self.status,
                self.detail)  # fmt: skip


class BrokerRecord:
    def __init__(self, store: Callable[[], DataStore], cache: Callable[[], DriveCache]):
        """Built on first use, so a closed day or an early start needs no Drive settings."""
        self._store, self._cache = store, cache

    @property
    def store(self) -> DataStore:
        return self._store()

    @property
    def cache(self) -> DriveCache:
        return self._cache()

    def done(self, day: date) -> set[tuple[str, float]]:
        """(structure, width) of every basket with an `ok` or `mismatch` result in the day's earlier records."""
        store, cache = self.store, self.cache
        prefix = f"{store.area}/{FOLDER}/{day.isoformat()}"
        report = cache.sync(prefix)
        if not report.complete:
            raise RecordProblem(UNREADABLE.format(problems="; ".join(report.problems)))
        found = set()
        for receipt in cache.receipts.under(prefix):
            text = cache.local(receipt.path).read_text(encoding="utf-8")
            found |= {(row["structure"], float(row["width"])) for row in csv.DictReader(io.StringIO(text))
                      if row["status"] in DONE}  # fmt: skip
        return found

    def write(self, day: date, run: datetime, results: Sequence[BrokerResult]) -> str:
        """Saves the run's file once; returns its Drive path. Any failure is a `RecordProblem`."""
        out = io.StringIO()
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(result.as_row() for result in results)
        path = RECORD_PATH.format(as_of=day.isoformat(), run=run)
        try:
            return self.store.put(path, out.getvalue().encode("utf-8")).path
        except Exception as exc:  # Drive refused, sign-in expired, a receipt conflict: the data did not land
            raise RecordProblem(f"the record {path} was not saved: {type(exc).__name__}") from exc
