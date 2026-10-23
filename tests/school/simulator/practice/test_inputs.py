"""The practice run's inputs (MS-SIM-d1): stores only, the legacy day's index close, the drivers' spot history."""

import csv
import io
from datetime import date
from pathlib import Path

import pytest

from fno.constants import INDEX_FUTURE, PANEL_FORMAT_LEGACY
from fno.research_data.nifty_panel import DailyFiles
from fno.school.constants import RoadCode
from fno.school.contracts.roads import ROADS_BY_CODE
from fno.school.simulator.history import bhavcopy_chain
from fno.school.simulator.history.bhavcopy_chain import BhavcopyChain
from fno.school.simulator.practice import stores
from fno.school.simulator.practice.cached_chain import CachedChain
from fno.school.simulator.practice.index_closes import ArchivedIndexCloses
from fno.school.simulator.practice.spots import ChainSpotHistory
from fno.storage.raw_library import RawFileLibrary
from fno.storage.raw_source import RawFileSource
from fno.storage.raw_store import RawFileStore
from tests.school.simulator.history.test_bhavcopy_chain import record
from tests.school.simulator.source import builders as sb

LEGACY_DAY = date(2021, 6, 24)
NIFTY_M = ROADS_BY_CODE[RoadCode.NIFTY_MONTHLY]


class DictStore(RawFileStore):
    name = "dict store"

    def __init__(self, files=None):
        self.files = dict(files or {})

    def get(self, path):
        return self.files.get(path)

    def put(self, path, data):
        raise AssertionError("a practice run never writes the archive")


class FetchRaises(RawFileSource):
    name = "an NSE request"

    def fetch(self, path):
        raise AssertionError(f"NSE was asked for {path}")


def index_close_csv(nifty: float, bank: float) -> bytes:
    out = io.StringIO()
    writer = csv.DictWriter(out, ["Index Name", "Closing Index Value"])
    writer.writeheader()
    writer.writerows([{"Index Name": "Nifty 50", "Closing Index Value": nifty},
                      {"Index Name": "Nifty Bank", "Closing Index Value": bank}])  # fmt: skip
    return out.getvalue().encode()


def closes_of(files_by_day: dict) -> ArchivedIndexCloses:
    return ArchivedIndexCloses(
        DailyFiles("index-close", "idx", None, None, lambda day: ("ind_close.csv", files_by_day.get(day)))
    )


def test_a_missing_day_closes_the_road_and_nothing_is_fetched(monkeypatch):
    """Criterion 9: the library is stores plus a source that publishes nothing, so no request can be made."""
    library = RawFileLibrary([DictStore()], stores.StoredFilesOnly())
    chain = stores.build_history_chain(library)
    assert chain.day("NIFTY", date(2025, 6, 2)) is None  # not archived: nothing, and no request
    assert stores.build_stored_library([DictStore()]).source.name == "stored files only"
    with pytest.raises(AssertionError, match="NSE was asked"):
        RawFileLibrary([DictStore()], FetchRaises()).get(
            "any/path"
        )  # the planted source does raise: the test has teeth


def test_the_stores_module_never_builds_a_fetching_library():
    text = Path(stores.__file__).read_text(encoding="utf-8")
    assert "build_nse_" not in text.replace("`build_nse_*_library`", "") and "NseDailyFoSource(" not in text


def test_a_legacy_day_takes_its_index_close_from_the_archived_file(monkeypatch):
    legacy = [record(under=""), record(kind=INDEX_FUTURE, strike="", side="", under="")]
    monkeypatch.setattr(bhavcopy_chain, "read_fo_file", lambda name, data: legacy)
    fo = [DailyFiles(PANEL_FORMAT_LEGACY, "fo", None, None, lambda day: ("fo.csv", b"x"))]
    chain = BhavcopyChain(fo, index_close=closes_of({LEGACY_DAY: index_close_csv(15860.5, 34000.0)}))
    assert chain.day("NIFTY", LEGACY_DAY).index_close == 15860.5


def test_a_legacy_day_with_no_index_close_closes_the_road(monkeypatch):
    from fno.school.constants import ClosureReason
    from fno.school.simulator.source.catalogue import HistoricalRoadCatalogue
    from fno.school.simulator.windows import PracticeWindows

    legacy = [record(under="", expiry=date(2021, 6, 24)), record(kind=INDEX_FUTURE, strike="", side="", under="")]
    monkeypatch.setattr(bhavcopy_chain, "read_fo_file", lambda name, data: legacy)
    fo = [DailyFiles(PANEL_FORMAT_LEGACY, "fo", None, None, lambda day: ("fo.csv", b"x"))]
    chain = BhavcopyChain(fo, index_close=closes_of({}))
    cat = HistoricalRoadCatalogue(sb.CALENDAR_2021, chain, sb.TERMS, PracticeWindows())
    day = next(d for d in cat.day(LEGACY_DAY) if d.road.code is RoadCode.NIFTY_MONTHLY)
    assert day.status.closed_by is ClosureReason.CAPTURE_MISSING


def test_the_index_close_is_the_one_of_that_index_and_a_damaged_file_gives_none():
    closes = closes_of({LEGACY_DAY: index_close_csv(15860.5, 34000.0), date(2021, 6, 25): b"not,a,close\n"})
    assert closes("NIFTY", LEGACY_DAY) == 15860.5 and closes("BANKNIFTY", LEGACY_DAY) == 34000.0
    assert closes("NIFTY", date(2021, 6, 25)) is None and closes("NIFTY", date(2021, 6, 28)) is None
    assert closes("SENSEX", LEGACY_DAY) is None


def test_the_cached_chain_reads_each_day_once():
    inner = sb.DictChain(sb.chain("NIFTY"))
    cached = CachedChain(inner)
    cached.day("NIFTY", sb.SESSION), cached.day("NIFTY", sb.SESSION)
    assert inner.asked == [("NIFTY", sb.SESSION)]


def test_the_spot_history_is_the_closes_strictly_before_the_session():
    days = [date(2022, 3, d) for d in (1, 2, 3, 4, 7)]
    chain = sb.DictChain(*[sb.chain("NIFTY", d) for d in days])
    history = ChainSpotHistory(chain, sb.CALENDAR)
    points = history.spots(NIFTY_M, date(2022, 3, 7))
    assert [p.session for p in points] == days[:4] and all(p.spot == sb.SPOT for p in points)
    assert date(2022, 3, 7) not in [p.session for p in points]
    assert ("NIFTY", date(2022, 3, 7)) not in chain.asked  # the session itself is never even read


def test_a_session_with_no_archived_chain_adds_no_point_and_the_first_session_has_no_history():
    chain = sb.DictChain(sb.chain("NIFTY", date(2022, 3, 2)))
    points = ChainSpotHistory(chain, sb.CALENDAR).spots(NIFTY_M, date(2022, 3, 4))
    assert [p.session for p in points] == [date(2022, 3, 2)]
    assert ChainSpotHistory(sb.DictChain(), sb.CALENDAR).spots(NIFTY_M, date(2022, 3, 4)) == ()


def test_a_day_outside_the_files_coverage_is_not_even_asked_for():
    def never(day):
        raise AssertionError("the file for a day it does not cover was asked for")

    covered_from_2024 = ArchivedIndexCloses(DailyFiles("index-close", "idx", date(2024, 1, 1), None, never))
    assert covered_from_2024("NIFTY", LEGACY_DAY) is None
