"""Shared fixtures of the NIFTY panel tests (story A3): small real subsets of NSE files (rows copied unchanged from
the originals in the owner's Drive) for a regular day per format, a day with both formats, a Diwali muhurat Sunday
(2019-10-27), a Saturday Budget session (2020-02-01) and a Saturday DR-site session (2024-03-02)."""

import csv
import gzip
import io
import zipfile
from datetime import date
from pathlib import Path

from fno.research_data.calendar import SessionCalendar
from fno.research_data.nifty_panel import build_nifty_panel
from fno.research_data.panel_store import CsvGzPanelFolder
from fno.storage.raw_library import RawFileLibrary
from fno.storage.raw_source import NseDailyFoSource, NseIndexCloseSource, NseLegacyFoSource, RawFileSource
from fno.storage.raw_store import AreaStore, LocalFolderStore, RawFileStore
from fno.storage.wiring import RAW_AREA, build_file_exceptions, build_session_calendar, daily_files

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "nse_panel"
CALENDAR = build_session_calendar()  # the real NSE calendar: special sessions come from it, not from the test
LEGACY_GAP = date(2021, 3, 30)  # a real session with no old-format F&O file at NSE (sourced exception, A1)


class ReadOnlyDrive(RawFileStore):
    """The fixture tree as Drive: any write fails the test."""

    name = "fake Drive"

    def __init__(self, folder: Path, asked: list[str] | None = None):
        self.files, self.asked = AreaStore(LocalFolderStore(folder), RAW_AREA), asked if asked is not None else []

    def get(self, path):
        self.asked.append(path)
        return self.files.get(path)

    def put(self, path, data):
        raise AssertionError("the panel must never write to Drive")


class NoSource(RawFileSource):
    def fetch(self, path):
        return None  # NSE does not have it either


def inputs(folder: Path = FIXTURES, asked: list[str] | None = None):
    def files(label, source):
        return daily_files(label, source, RawFileLibrary([ReadOnlyDrive(folder, asked)], NoSource()))

    return [files("udiff", NseDailyFoSource), files("legacy", NseLegacyFoSource)], files(
        "index-close", NseIndexCloseSource
    )


def build(out: Path, start: date, end: date | None = None, *, folder=FIXTURES, calendar=CALENDAR, exceptions=None):
    fo, index = inputs(folder)
    exceptions = build_file_exceptions() if exceptions is None else exceptions
    sink = CsvGzPanelFolder(out)
    return build_nifty_panel(fo, index, start, end or start, calendar=calendar, exceptions=exceptions, sink=sink)


def panel_rows(out: Path, year: int, table: str = "options") -> list[dict]:
    with gzip.open(out / f"{table}_{year}.csv.gz", "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def raw(dataset: str, day: date, filename: str) -> bytes:
    return (FIXTURES / RAW_AREA / RawFileSource.dated_path(dataset, day, filename)).read_bytes()


def nifty_rows_in(dataset: str, day: date, filename: str, futures: bool = False) -> list[dict]:
    """NIFTY option (or future) rows counted straight from the file, without the panel's reader."""
    with zipfile.ZipFile(io.BytesIO(raw(dataset, day, filename))) as z:
        rows = list(csv.DictReader(io.StringIO(z.read(z.namelist()[0]).decode("utf-8-sig"))))
    if "INSTRUMENT" in rows[0]:
        return [r for r in rows if r["INSTRUMENT"] == ("FUTIDX" if futures else "OPTIDX") and r["SYMBOL"] == "NIFTY"]
    return [r for r in rows if r["FinInstrmTp"] == ("IDF" if futures else "IDO") and r["TckrSymb"] == "NIFTY"]


class FixtureCalendar(SessionCalendar):
    """Only the given days are sessions (to build several fixture days in one panel)."""

    def __init__(self, kinds: dict[date, str]):
        self.kinds = kinds

    def session_kind(self, day):
        return self.kinds.get(day)

    def calendar_sha256(self):
        return "fixture"


DAYS = {
    date(2019, 1, 2): (NseLegacyFoSource, "legacy", "regular"),
    date(2019, 10, 27): (NseLegacyFoSource, "legacy", "muhurat"),
    date(2020, 2, 1): (NseLegacyFoSource, "legacy", "special"),
    date(2024, 1, 2): (NseDailyFoSource, "udiff", "regular"),
    date(2024, 3, 2): (NseDailyFoSource, "udiff", "special"),
}


DAYS = {
    date(2019, 1, 2): (NseLegacyFoSource, "legacy", "regular"),
    date(2019, 10, 27): (NseLegacyFoSource, "legacy", "muhurat"),
    date(2020, 2, 1): (NseLegacyFoSource, "legacy", "special"),
    date(2024, 1, 2): (NseDailyFoSource, "udiff", "regular"),
    date(2024, 3, 2): (NseDailyFoSource, "udiff", "special"),
}
