"""The contracts NSE listed, read from the previous session's archived F&O file (judge 483 findings 1 and 2)."""

import io
import zipfile
from datetime import date

import pytest
import requests

from fno.fo_bhavcopy import COLUMNS
from fno.school.constants import OptionKind, RoadCode
from fno.school.contracts.roads import ROADS_BY_CODE
from fno.school.contracts.snapshot import ContractKey
from fno.school.quality.ports import ListedContracts, ListingUnavailable
from fno.school.roads.expiries import ListedRoadExpiries
from fno.school.roads.listed_contracts import NseListedContracts
from fno.school.roads.ports import ExpiryUnavailable
from fno.school.roads.stored_files import StoredFilesOnly
from fno.storage.raw_library import RawFileLibrary
from fno.storage.raw_source import NseDailyFoSource
from fno.storage.raw_store import RawFileStore
from tests.school.roads.test_lots_and_expiries import HistoryFake, ListedFake

SESSION = date(2026, 10, 22)
PREVIOUS = date(2026, 10, 21)
NEAR, FAR = date(2026, 10, 27), date(2026, 11, 24)


def fo_row(symbol, kind, expiry, strike="", option=""):
    row = dict.fromkeys(COLUMNS, "")
    row.update(TradDt=PREVIOUS.isoformat(), FinInstrmTp=kind, TckrSymb=symbol, XpryDt=expiry.isoformat(),
               StrkPric=strike, OptnTp=option, ClsPric="10.00", SttlmPric="10.00", TtlTradgVol="5")  # fmt: skip
    return row


def zipped(day: date, rows) -> bytes:
    lines = [",".join(COLUMNS)] + [",".join(r[c] for c in COLUMNS) for r in rows]
    name = NseDailyFoSource.filename_for(day)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        archive.writestr(name.removesuffix(".zip"), ("\n".join(lines) + "\n").encode())
    return out.getvalue()


class Files(RawFileStore):
    name = "files"

    def __init__(self, files, error=None):
        self.files, self.error = files, error

    def get(self, path):
        if self.error:
            raise self.error
        return self.files.get(path)

    def put(self, path, data):
        raise AssertionError("never written")


def listing(files, error=None) -> NseListedContracts:
    return NseListedContracts(RawFileLibrary([Files(files, error)], StoredFilesOnly()))


def rows():
    out = [fo_row("FINNIFTY", "IDF", NEAR)]  # a future is not an option
    for expiry in (NEAR, FAR):
        for strike in (24000, 24050, 24100, 27000):  # 27000 is far outside the recorder's 5% band
            for option in ("CE", "PE"):
                out.append(fo_row("FINNIFTY", "IDO", expiry, str(strike), option))
    out.append(fo_row("NIFTY", "IDO", NEAR, "24050", "CE"))  # another underlying
    return out


def test_it_lists_the_option_contracts_of_the_underlying_and_expiries_within_the_recorders_band_of_the_spot():
    source = listing({NseDailyFoSource.path_for(PREVIOUS): zipped(PREVIOUS, rows())})
    assert isinstance(source, ListedContracts)
    found = source.contracts("FINNIFTY", (NEAR,), SESSION, 24050.0)
    assert found == {ContractKey(NEAR, float(s), kind) for s in (24000, 24050, 24100) for kind in OptionKind}


def test_the_recorders_band_moves_with_the_spot():
    source = listing({NseDailyFoSource.path_for(PREVIOUS): zipped(PREVIOUS, rows())})
    far = source.contracts("FINNIFTY", (NEAR,), SESSION, 27000.0)
    assert {k.strike for k in far} == {27000.0}  # 5% either side of 27,000 holds only that strike


def test_a_holiday_before_the_session_looks_back_to_the_last_file():
    earlier = date(2026, 10, 19)
    source = listing({NseDailyFoSource.path_for(earlier): zipped(earlier, rows())})
    assert source.contracts("FINNIFTY", (NEAR,), SESSION, 24050.0)


@pytest.mark.parametrize("files", [{}, {NseDailyFoSource.path_for(PREVIOUS): b"not a zip"}], ids=["no file", "damaged"])
def test_a_missing_or_damaged_file_is_listing_unavailable(files):
    with pytest.raises(ListingUnavailable):
        listing(files).contracts("FINNIFTY", (NEAR,), SESSION, 24050.0)


def test_a_file_without_the_underlying_or_the_expiry_is_listing_unavailable():
    source = listing({NseDailyFoSource.path_for(PREVIOUS): zipped(PREVIOUS, rows())})
    with pytest.raises(ListingUnavailable):
        source.contracts("BANKNIFTY", (NEAR,), SESSION, 55000.0)
    with pytest.raises(ListingUnavailable):
        source.contracts("FINNIFTY", (date(2027, 1, 26),), SESSION, 24050.0)


def test_a_drive_reply_that_is_not_json_is_an_outage_not_a_listing_problem():
    error = requests.JSONDecodeError("Expecting value", "<html>proxy</html>", 0)
    assert isinstance(error, ValueError) and isinstance(error, requests.RequestException)
    with pytest.raises(requests.RequestException):
        listing({}, error).contracts("FINNIFTY", (NEAR,), SESSION, 24050.0)


def test_the_expiry_source_lets_a_non_json_drive_reply_through_but_closes_on_an_unreadable_listing_file():
    error = requests.JSONDecodeError("Expecting value", "<html>proxy</html>", 0)

    class Down(ListedFake):
        def listed(self, underlying, today):
            raise error

    road = ROADS_BY_CODE[RoadCode.NIFTY_MONTHLY]
    from fno.quotes.monthly_contracts import PointInTimeMonthlies

    with pytest.raises(requests.RequestException):
        ListedRoadExpiries(Down({}), PointInTimeMonthlies(HistoryFake({}))).expected(road, SESSION)

    class Damaged(ListedFake):
        def listed(self, underlying, today):
            raise zipfile.BadZipFile("File is not a zip file")

    with pytest.raises(ExpiryUnavailable):
        ListedRoadExpiries(Damaged({}), PointInTimeMonthlies(HistoryFake({}))).expected(road, SESSION)
