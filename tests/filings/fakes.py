"""Fakes for the filings archive tests: an exchange list, NSE's XBRL host and a clock (story A12)."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from fno.constants import CONSOLIDATED, FILING_RESULTS
from fno.filings.archive import FilingArchive
from fno.filings.filing import Filing
from fno.filings.index import FilingIndex
from fno.filings.manifest import FilingManifest
from fno.filings.sources import NSE_XBRL_FOLDER, NseFilingFileSource
from fno.models import IST
from fno.storage.raw_store import LocalFolderStore

SINCE = date(2023, 10, 1)


def filing(symbol: str, name: str, filed: datetime, period=date(2025, 9, 30), kind=FILING_RESULTS) -> Filing:
    return Filing(kind, symbol, period, filed, NSE_XBRL_FOLDER + name, CONSOLIDATED if kind == FILING_RESULTS else "")


def at(day: int, hour: int = 18) -> datetime:
    return datetime(2025, 10, day, hour, tzinfo=IST)


class FakeIndex(FilingIndex):
    name, kind = "fake list", FILING_RESULTS

    def __init__(self, by_symbol: dict, error: Exception | None = None):
        super().__init__(lambda path, params: None)
        self.by_symbol, self.error = by_symbol, error

    def filings(self, symbol: str, since: date) -> list[Filing]:
        if self.error:
            raise self.error
        return [f for f in self.by_symbol.get(symbol, []) if f.filed_at.date() >= since]


class FakeXbrlHost(NseFilingFileSource):
    """NSE's XBRL folder: serves the given files by name, counts what was asked."""

    def __init__(self, files: dict[str, bytes]):
        super().__init__(session=None)
        self.files, self.fetched = files, []

    def fetch(self, path: str) -> bytes | None:
        name = path.rsplit("/", 1)[-1]
        self.fetched.append(name)
        return self.files.get(name)


class StepClock:
    """Each reading is one minute later."""

    def __init__(self, start: datetime = datetime(2026, 10, 13, 9, tzinfo=IST)):
        self.now = start

    def __call__(self) -> datetime:
        self.now += timedelta(minutes=1)
        return self.now


def archive(tmp_path, clock) -> FilingArchive:
    return FilingArchive(LocalFolderStore(tmp_path / "drive"), FilingManifest(tmp_path / "manifests"), clock)
