"""The archived F&O files as the simulator's chain (MS-SIM-a)."""

from datetime import date

import pytest

from fno.constants import INDEX_FUTURE, INDEX_OPTION
from fno.research_data.nifty_panel import DailyFiles
from fno.school.constants import ExpiryKind, OptionKind
from fno.school.simulator.history import bhavcopy_chain, edge1
from fno.school.simulator.history.bhavcopy_chain import BhavcopyChain
from fno.school.simulator.history.ports import HistoricalChain

DAY, MONTHLY, WEEKLY = date(2024, 3, 4), date(2024, 3, 28), date(2024, 3, 7)


def record(symbol="NIFTY", kind=INDEX_OPTION, expiry=MONTHLY, strike="22000", side="CE", close="100", volume="5",
           oi="50", lot="", under="22100"):  # fmt: skip
    return {"TckrSymb": symbol, "FinInstrmTp": kind, "XpryDt": expiry.isoformat(), "StrkPric": strike, "OptnTp": side,
            "ClsPric": close, "TtlTradgVol": volume, "OpnIntrst": oi, "NewBrdLotQty": lot, "UndrlygPric": under,
            "SttlmPric": close, "TtlTrfVal": "0"}  # fmt: skip


RECORDS = [
    record(kind=INDEX_FUTURE, strike="", side="", lot="25"),
    record(),
    record(strike="22000", side="PE", volume="0", close="0"),
    record(expiry=WEEKLY, strike="22100"),
    record(symbol="BANKNIFTY", strike="48000"),
    record(symbol="NIFTY", kind="STO"),
]


def files_of(records, covers=True, data=b"x"):
    return DailyFiles("udiff", "fo", None, None, lambda day: ("file.csv", data if covers else None))


@pytest.fixture
def chain(monkeypatch):
    monkeypatch.setattr(bhavcopy_chain, "read_fo_file", lambda name, data: RECORDS)
    return BhavcopyChain([files_of(RECORDS)])


def test_it_is_a_historical_chain(chain):
    assert isinstance(chain, HistoricalChain)


def test_only_the_underlyings_index_options_are_rows_and_a_zero_volume_leg_is_kept_as_such(chain):
    day = chain.day("NIFTY", DAY)
    assert {(r.strike, r.kind, r.volume) for r in day.rows if r.expiry == MONTHLY} == {
        (22000.0, OptionKind.CALL, 5), (22000.0, OptionKind.PUT, 0)}  # fmt: skip
    assert len(day.rows) == 3 and day.underlying == "NIFTY" and day.index_close == 22100.0


def test_an_expiry_with_a_future_is_monthly_the_other_is_weekly(chain):
    day = chain.day("NIFTY", DAY)
    assert day.expiries(ExpiryKind.MONTHLY) == (MONTHLY,) and day.expiries(ExpiryKind.WEEKLY) == (WEEKLY,)


def test_a_lot_is_the_one_the_file_states_and_never_derived(chain):
    assert chain.day("NIFTY", DAY).lots == {MONTHLY: 25}
    assert chain.day("BANKNIFTY", DAY).lots == {}


def test_a_day_with_no_file_or_no_rows_for_the_underlying_is_none(monkeypatch):
    monkeypatch.setattr(bhavcopy_chain, "read_fo_file", lambda name, data: RECORDS)
    assert BhavcopyChain([files_of(RECORDS, covers=False)]).day("NIFTY", DAY) is None
    assert BhavcopyChain([files_of(RECORDS)]).day("FINNIFTY", DAY) is None
    assert BhavcopyChain([]).day("NIFTY", DAY) is None


def test_a_damaged_file_is_skipped_for_the_next_format(monkeypatch):
    def reader(name, data):
        if data == b"bad":
            raise bhavcopy_chain.BadFile("damaged")
        return RECORDS

    monkeypatch.setattr(bhavcopy_chain, "read_fo_file", reader)
    both = [files_of(RECORDS, data=b"bad"), files_of(RECORDS)]
    assert BhavcopyChain(both).day("NIFTY", DAY) is not None


def test_a_legacy_day_without_an_underlying_price_takes_the_index_close_it_is_given(monkeypatch):
    legacy = [record(under=""), record(kind=INDEX_FUTURE, strike="", side="", under="")]
    monkeypatch.setattr(bhavcopy_chain, "read_fo_file", lambda name, data: legacy)
    assert BhavcopyChain([files_of(legacy)]).day("NIFTY", DAY).index_close is None
    given = BhavcopyChain([files_of(legacy)], index_close=lambda day: 22000.5)
    assert given.day("NIFTY", DAY).index_close == 22000.5


def test_the_monthly_rows_match_edge1s_own_reader_on_the_same_records(chain):
    theirs = edge1.module("day_files").rows_of(DAY, RECORDS, "NIFTY", "udiff")
    ours = [r for r in chain.day("NIFTY", DAY).rows if r.monthly]
    assert sorted((q.expiry, q.strike, q.kind, q.close, q.volume, q.open_interest) for q in theirs.options) == sorted(
        (r.expiry, r.strike, str(r.kind), r.close, r.volume, r.open_interest) for r in ours)  # fmt: skip


def test_a_number_that_is_not_one_makes_the_file_unreadable_for_that_format(monkeypatch):
    bad = [record(close="12x"), record(kind=INDEX_FUTURE, strike="", side="")]
    monkeypatch.setattr(bhavcopy_chain, "read_fo_file", lambda name, data: bad)
    assert BhavcopyChain([files_of(bad)]).day("NIFTY", DAY) is None


def test_the_index_close_comes_from_the_nearest_expiry_whatever_the_row_order(monkeypatch):
    far = record(expiry=date(2024, 4, 25), under="22300")
    near = record(under="22100")
    fut = record(kind=INDEX_FUTURE, strike="", side="")
    for order in ([far, near, fut], [near, far, fut]):
        monkeypatch.setattr(bhavcopy_chain, "read_fo_file", lambda name, data, rows=order: rows)
        assert BhavcopyChain([files_of(order)]).day("NIFTY", DAY).index_close == 22100.0
