"""Which raw NSE files the archive is missing or holds damaged, against NSE's session calendar (story A1).

Read-only: it only calls `RawFileStore.get`. A session without a file fails unless a sourced exception explains it;
a file on a day the calendar calls closed is reported for review.
"""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from ..research_data.calendar import SessionCalendar
from .raw_source import NseArchiveSource
from .raw_store import RawFileStore

EXCEPTION_FIELDS = ("dataset", "date", "reason", "source_url")
TABLE_HEADER = f"{'dataset':<36} {'from':>10} {'to':>10} {'expected':>8} {'present':>7} {'missing':>7} {'damaged':>7}"

Validator = Callable[[str, bytes], None]  # raises ValueError when the file is damaged or not in its schema


@dataclass(frozen=True)
class CoverageDataset:
    source: type[NseArchiveSource]
    validate: Validator


@dataclass
class DatasetCoverage:
    dataset: str
    start: date
    end: date
    expected: int = 0
    present: int = 0
    missing: list[date] = field(default_factory=list)
    damaged: list[tuple[date, str]] = field(default_factory=list)
    excepted: list[tuple[date, str]] = field(default_factory=list)
    unexpected: list[date] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (self.missing or self.damaged)


def read_fingerprints(path: Path) -> dict[str, str]:
    """NSE file name -> SHA-256, from a laptop tool manifest (`date,url,status,sha256,...`; rows with status 200)."""
    if not path.is_file():
        return {}
    rows = csv.DictReader(path.read_text(encoding="utf-8").splitlines())
    return {r["url"].rsplit("/", 1)[-1]: r["sha256"] for r in rows if r["status"] == "200" and r["sha256"]}


@dataclass(frozen=True)
class FingerprintCheck:
    """A validator that also requires a file's SHA-256 to match the manifest, where the manifest has the file."""

    validate: Validator
    fingerprints: dict[str, str]

    def __call__(self, filename: str, data: bytes) -> None:
        want = self.fingerprints.get(filename)
        if want and hashlib.sha256(data).hexdigest() != want:
            raise ValueError(f"{filename}: SHA-256 differs from the manifest")
        self.validate(filename, data)


def read_exceptions(path: Path) -> dict[tuple[str, date], str]:
    """(dataset, day) -> reason, for sessions NSE never published a file for; each row needs a source link."""
    if not path.is_file():
        return {}
    exceptions = {}
    for number, row in enumerate(csv.DictReader(path.read_text(encoding="utf-8").splitlines()), start=2):
        if tuple(row) != EXCEPTION_FIELDS or not (row["source_url"] or "").startswith("https://"):
            raise ValueError(f"{path.name} line {number}: needs {','.join(EXCEPTION_FIELDS)} with an https source")
        exceptions[(row["dataset"], date.fromisoformat(row["date"]))] = row["reason"]
    return exceptions


DEFAULT_WORKERS = 8  # files read at the same time (Drive allows far more requests per minute than this makes)


class CoverageCheck:
    def __init__(
        self,
        store: RawFileStore,
        calendar: SessionCalendar,
        exceptions: dict[tuple[str, date], str],
        workers: int = DEFAULT_WORKERS,
    ):
        self.store, self.calendar, self.exceptions, self.workers = store, calendar, exceptions, workers

    def run(self, dataset: CoverageDataset, start: date, end: date) -> DatasetCoverage:
        source = dataset.source
        start = max(start, source.first_day or start)
        end = min(end, source.last_day or end)
        result = DatasetCoverage(source.dataset, start, end)
        days = [start + timedelta(offset) for offset in range((end - start).days + 1)]
        with ThreadPoolExecutor(max_workers=self.workers) as pool:  # reads in parallel, results in day order
            for day, data in zip(days, pool.map(lambda d: self.store.get(source.path_for(d)), days)):
                self._check_day(dataset, day, data, result)
        return result

    def _check_day(self, dataset: CoverageDataset, day: date, data: bytes | None, result: DatasetCoverage) -> None:
        source = dataset.source
        if not self.calendar.is_session(day):
            if data is not None:
                result.unexpected.append(day)
            return
        result.expected += 1
        if data is None:
            reason = self.exceptions.get((source.dataset, day))
            if reason:
                result.excepted.append((day, reason))
            else:
                result.missing.append(day)
            return
        try:
            dataset.validate(source.filename_for(day), data)
        except ValueError as exc:
            result.damaged.append((day, str(exc)))
            return
        result.present += 1


def report_lines(results: list[DatasetCoverage]) -> list[str]:
    lines = [TABLE_HEADER]
    for r in results:
        lines.append(
            f"{r.dataset:<36} {r.start:%Y-%m-%d} {r.end:%Y-%m-%d} {r.expected:>8} {r.present:>7} "
            f"{len(r.missing):>7} {len(r.damaged):>7}"
        )
    for r in results:
        lines += [f"missing  {r.dataset} {day}" for day in r.missing]
        lines += [f"damaged  {r.dataset} {day}: {reason}" for day, reason in r.damaged]
        lines += [f"excepted {r.dataset} {day}: {reason}" for day, reason in r.excepted]
        lines += [f"unexpected file (calendar says closed; review) {r.dataset} {day}" for day in r.unexpected]
    verdict = "complete" if all(r.ok for r in results) else "INCOMPLETE: missing or damaged files above"
    return [*lines, f"result: {verdict}"]
