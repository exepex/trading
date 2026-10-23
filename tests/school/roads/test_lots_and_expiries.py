"""The two sources behind the catalogue (story 3.5): the dated lot from A20a's archive and the listed expiries."""

from datetime import date

import pytest

from fno.quotes.expiry_listing import ExpiryHistory, ExpiryListUnavailable, ListedExpiries
from fno.quotes.monthly_contracts import PointInTimeMonthlies
from fno.school.constants import RoadCode
from fno.school.contracts.roads import ROADS_BY_CODE
from fno.school.roads.expiries import ListedRoadExpiries
from fno.school.roads.lots import ArchivedLots, month_label
from fno.school.roads.ports import ExpirySource, ExpiryUnavailable, LotSource
from fno.school.roads.stored_files import StoredFilesOnly
from fno.storage.raw_library import RawFileLibrary
from fno.storage.snapshot_source import FoLotSizeSource
from tests.school.roads.capture_builder import DictStore

SESSION = date(2026, 10, 22)
LOT_FILE = (
    b"UNDERLYING                          ,SYMBOL    ,OCT-26     ,NOV-26     ,DEC-26     \n"
    b"NIFTY 50                            ,NIFTY     ,65         ,65         ,65         \n"
    b"Nifty Bank                          ,BANKNIFTY ,30         ,30         ,35         \n"
    b"Nifty Midcap Select                 ,MIDCPNIFTY,120        ,           ,120        \n"
)


def archive(files: dict) -> ArchivedLots:
    store = DictStore()
    store.files.update(files)
    return ArchivedLots(RawFileLibrary([store], StoredFilesOnly()))


def lots_file(day=SESSION, data=LOT_FILE):
    return {FoLotSizeSource.path_for(day): data}


def test_the_lot_is_the_one_every_used_expiry_month_carries_with_its_source_path():
    lot = archive(lots_file()).lot("NIFTY", SESSION, (date(2026, 10, 27), date(2026, 11, 24)))
    assert lot.units == 65 and lot.source == FoLotSizeSource.path_for(SESSION)


def test_a_lot_of_zero_is_no_lot():
    data = LOT_FILE.replace(b"65         ,65         ,65", b"0          ,0          ,0")
    assert archive(lots_file(data=data)).lot("NIFTY", SESSION, (date(2026, 10, 27),)) is None


def test_an_outage_reading_the_listing_is_not_turned_into_a_closure():
    class Down(ListedFake):
        def listed(self, underlying, today):
            raise ConnectionError("drive unreachable")

    source = ListedRoadExpiries(Down({}), PointInTimeMonthlies(HistoryFake({})))
    with pytest.raises(ConnectionError):
        source.expected(ROADS_BY_CODE[RoadCode.NIFTY_MONTHLY], SESSION)


@pytest.mark.parametrize(
    "underlying,expiries",
    [
        ("BANKNIFTY", (date(2026, 11, 24), date(2026, 12, 29))),  # 30 against 35: no single lot
        ("MIDCPNIFTY", (date(2026, 10, 27), date(2026, 11, 24))),  # a blank cell for November
        ("NIFTY", (date(2027, 3, 30),)),  # a month the file has no column for
        ("SENSEX", (date(2026, 10, 27),)),  # an underlying the file has no row for
    ],
)
def test_no_single_lot_means_none(underlying, expiries):
    assert archive(lots_file()).lot(underlying, SESSION, expiries) is None


def test_a_session_without_its_own_copy_has_no_lot_even_when_another_day_has_one():
    lots = archive(lots_file(day=date(2026, 10, 21)))
    assert lots.lot("NIFTY", SESSION, (date(2026, 10, 27),)) is None


def test_a_damaged_lot_file_has_no_lot():
    assert archive(lots_file(data=b"nonsense,\n1,2\n")).lot("NIFTY", SESSION, (date(2026, 10, 27),)) is None


def test_month_labels_are_nse_s_whatever_the_locale():
    assert [month_label(date(2026, m, 1)) for m in (1, 5, 12)] == ["JAN-26", "MAY-26", "DEC-26"]


def test_stored_files_only_never_fetches_anything():
    assert StoredFilesOnly().fetch("any/path") is None
    assert RawFileLibrary([], StoredFilesOnly()).get("nse/anything.csv").data is None


def test_lot_source_and_expiry_source_ports():
    assert isinstance(archive({}), LotSource)
    assert isinstance(ListedRoadExpiries(ListedFake({}), PointInTimeMonthlies(HistoryFake({}))), ExpirySource)


class ListedFake(ListedExpiries):
    def __init__(self, by_underlying, fail=False):
        self.by_underlying, self.fail = by_underlying, fail

    def listed(self, underlying, today):
        if self.fail:
            raise ExpiryListUnavailable("no NSE file")
        return list(self.by_underlying[underlying]), {"file": "fixture"}


class HistoryFake(ExpiryHistory):
    """Every earlier file lists the same expiries, 60+ days ahead for the monthlies: A5 sees them as monthly."""

    def __init__(self, by_underlying):
        self.by_underlying = by_underlying

    def listed_on(self, underlying, day):
        return day, list(self.by_underlying[underlying]), {"file": "fixture"}


LISTED = [date(2026, 10, 27), date(2026, 11, 3), date(2026, 11, 9), date(2026, 11, 24), date(2026, 12, 29)]


def expected(code, listed=LISTED, fail=False):
    monthlies = [date(2026, 10, 27), date(2026, 11, 24), date(2026, 12, 29)]
    source = ListedRoadExpiries(
        ListedFake({"NIFTY": listed}, fail), PointInTimeMonthlies(HistoryFake({"NIFTY": monthlies}))
    )
    return source.expected(ROADS_BY_CODE[code], SESSION)


def test_monthly_roads_record_the_two_nearest_monthlies():
    assert expected(RoadCode.NIFTY_MONTHLY) == (date(2026, 10, 27), date(2026, 11, 24))


def test_the_weekly_road_records_the_two_nearest_non_monthly_expiries_after_today():
    assert expected(RoadCode.NIFTY_WEEKLY) == (date(2026, 11, 3), date(2026, 11, 9))


def test_an_unreadable_listing_is_expiry_unavailable_not_a_guess():
    with pytest.raises(ExpiryUnavailable):
        expected(RoadCode.NIFTY_MONTHLY, fail=True)
