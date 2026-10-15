"""R2 snapshot capture (fake Groww source), reference inputs and the hash-checked input cache."""

import hashlib
import json
from datetime import date, datetime, timedelta

import pytest
from r2_synthetic import weekdays
from r2study.bhav import DaySummary, Future
from r2study.inputs import DatasetFiles, HashMismatch, InputCache
from r2study.sessions import Sessions
from r2study.snapshot_capture import Candidate, OutsideWindow, candidates, capture, check_window, snapshot_strikes
from r2study.sources import CorporateActions, SymbolNames, read_filing_times, read_meetings

from fno.market_read_models.corporate_actions import CorporateAction
from fno.market_read_models.symbol_changes import SymbolChange

SESSIONS = Sessions(weekdays(date(2026, 10, 1), date(2026, 12, 31)))
TODAY = date(2026, 10, 15)
PREVIOUS = DaySummary(
    date(2026, 10, 14),
    {
        "ABC": [Future(date(2026, 10, 27), 1000.0, 1000.0, 10, 1, 1, 100),
                Future(date(2026, 11, 24), 1000.0, 1000.0, 10, 1, 1, 125)],
        "FUT": [Future(date(2026, 10, 27), 1, 1, 1, 1, 1, 5)],
    },
    frozenset({"ABC"}),
)  # fmt: skip


def row(symbol, day, purpose="Financial Results"):
    return {"symbol": symbol, "purpose": purpose, "bm_desc": "", "date": day}


def test_candidates_are_fo_stocks_with_results_in_the_next_10_sessions():
    tenth = SESSIONS.ahead(TODAY, 10)[-1]
    rows = [
        row("ABC", f"{tenth:%d-%b-%Y}"),  # the 10th session: in
        row("FUT", f"{tenth:%d-%b-%Y}"),  # futures only: out
        row("ABC", f"{TODAY:%d-%b-%Y}"),  # today: out (duplicates keep the first in range)
        row("XYZ", "20-Oct-2026"),  # not F&O
        row("ABC", f"{tenth + timedelta(days=1):%d-%b-%Y}"),
    ]
    assert candidates(rows, TODAY, SESSIONS, PREVIOUS) == [Candidate("ABC", tenth)]
    late = [row("ABC", f"{SESSIONS.after(tenth):%d-%b-%Y}"), row("ABC", "20-Oct-2026", "Dividend")]
    assert candidates(late, TODAY, SESSIONS, PREVIOUS) == []


def test_snapshot_strikes_cover_three_steps_each_side_that_are_listed():
    assert snapshot_strikes([940, 960, 980, 1000, 1020, 1040, 1060, 1080], 1003.0) == [
        (-3, 940.0), (-2, 960.0), (-1, 980.0), (0, 1000.0), (1, 1020.0), (2, 1040.0), (3, 1060.0),
    ]  # fmt: skip
    assert snapshot_strikes([], 1000.0) == []


class FakeGroww:
    def __init__(self):
        self.calls = 0

    def expiries(self, symbol):
        return [date(2026, 10, 27), date(2026, 11, 24)]

    def chain_symbols(self, symbol, expiry):
        return 1001.0, {(float(k), kind): f"{symbol}{k}{kind}" for k in range(940, 1081, 20) for kind in ("CE", "PE")}

    def quote(self, trading_symbol):
        self.calls += 1
        return {"bid_price": 9.5, "offer_price": 10.5, "bid_quantity": 200, "offer_quantity": 300}


def clock_from(start: datetime, step_seconds: int):
    moments = iter(start + timedelta(seconds=step_seconds * i) for i in range(10_000))
    return lambda: next(moments)


def test_capture_quotes_14_legs_on_the_rule_expiry_and_stops_at_15_00():
    source = FakeGroww()
    found = [Candidate("ABC", date(2026, 10, 20))]  # R 21 Oct: 27 Oct is only 4 sessions after -> November
    raw, legs = capture(source, found, SESSIONS, PREVIOUS, {}, clock_from(datetime(2026, 10, 15, 14, 0), 1))
    stock = raw["stocks"][0]
    assert stock["expiry"] == "2026-11-24" and stock["pushed"] is True
    assert len(legs) == 14 and legs[0].lot == 125  # the chosen (November) expiry's own lot, not October's 100
    assert (raw["after_window"], raw["errors"], raw["stocks_skipped"], raw["no_previous_row"]) == (0, 0, 0, 14)
    late = capture(FakeGroww(), found, SESSIONS, PREVIOUS, {}, clock_from(datetime(2026, 10, 15, 14, 59, 50), 1))
    assert late[0]["after_window"] > 0 and len(late[1]) + late[0]["after_window"] == 14


def test_a_quote_that_comes_back_at_15_00_is_dropped_and_errors_are_counted_not_one_sided():
    found = [Candidate("ABC", date(2026, 10, 20))]
    source = FakeGroww()
    raw, legs = capture(source, found, SESSIONS, PREVIOUS, {}, clock_from(datetime(2026, 10, 15, 14, 59, 58), 1))
    assert legs == [] and raw["after_window"] == 14  # asked at 14:59:59, answered at 15:00:00: dropped
    assert source.calls == 1  # nothing is asked once 15:00 has passed

    class Failing(FakeGroww):
        def quote(self, trading_symbol):
            raise ConnectionError("down")

    raw, legs = capture(Failing(), found, SESSIONS, PREVIOUS, {}, clock_from(datetime(2026, 10, 15, 14, 0), 1))
    assert legs == [] and raw["errors"] == 14

    class NoChain(FakeGroww):
        def expiries(self, symbol):
            raise RuntimeError("token refused")

    raw, _ = capture(NoChain(), found, SESSIONS, PREVIOUS, {}, clock_from(datetime(2026, 10, 15, 14, 0), 1))
    assert raw["stocks_skipped"] == 1 and raw["stocks"][0]["skipped"] == "error RuntimeError"


def test_snapshot_window_is_14_to_15_ist_on_a_session():
    check_window(datetime(2026, 10, 15, 14, 0), SESSIONS)
    for moment in (datetime(2026, 10, 15, 13, 59), datetime(2026, 10, 15, 15, 0), datetime(2026, 10, 17, 14, 30)):
        with pytest.raises(OutsideWindow):
            check_window(moment, SESSIONS)


def test_board_meeting_rows_and_skipped_rows_are_counted():
    data = json.dumps([{"bm_symbol": "ABC", "bm_date": "22-Oct-2024", "bm_purpose": "Financial Results"},
                       {"bm_symbol": "", "bm_date": "22-Oct-2024"}]).encode()  # fmt: skip
    (meeting,), skipped = read_meetings(data)
    assert skipped == 1 and read_meetings(b"[]") == ([], 0)
    assert (meeting.symbol, meeting.day) == ("ABC", date(2024, 10, 22)) and "Financial Results" in meeting.text


def test_filing_times_are_ist_without_timezone(tmp_path):
    manifest = tmp_path / "results-xbrl.csv"
    manifest.write_text(
        "symbol,period_end,filed_at\nABC,2024-09-30,2024-10-22T17:05:00+05:30\nABC,2024-09-30,2024-10-22T11:35:00+00:00\n"
        "XYZ,2024-09-30,\n"
    )
    moment = datetime(2024, 10, 22, 17, 5)
    assert read_filing_times(manifest) == {"ABC": [(moment, date(2024, 9, 30)), (moment, date(2024, 9, 30))]}


def test_renamed_symbols_and_corporate_actions_join_on_the_latest_name():
    names = SymbolNames([SymbolChange("OLD", "MID", date(2023, 1, 2)), SymbolChange("MID", "NEW", date(2025, 6, 2))])
    assert names("OLD", date(2022, 5, 1)) == "NEW" and names("MID", date(2025, 6, 2)) == "MID"
    assert names("NEW", date(2020, 1, 1)) == "NEW"
    actions = CorporateActions(
        [CorporateAction("MID", date(2025, 10, 3), "Bonus 1:1", "ratio", 2.0),
         CorporateAction("NEW", date(2025, 10, 6), "Dividend - Rs 5", "none"),
         CorporateAction("NEW", date(2025, 10, 8), "Rights 1:5 @ premium Rs 10", "none")],
        names,
    )  # fmt: skip
    assert actions.between("MID", date(2025, 10, 2), date(2025, 10, 3))  # ex-date on R: inside
    assert not actions.between("MID", date(2025, 10, 3), date(2025, 10, 6))  # ex-date on entry: outside
    assert not actions.between("NEW", date(2025, 10, 5), date(2025, 10, 7))  # a dividend changes no contract
    assert actions.between("NEW", date(2025, 10, 7), date(2025, 10, 8))  # rights do
    assert not CorporateActions.covers(date(2025, 9, 5), date(2025, 9, 9))


def test_input_cache_refuses_a_file_whose_hash_differs_from_its_manifest(tmp_path):
    manifests = tmp_path / "manifests"
    manifests.mkdir()
    good = b"file bytes"
    (manifests / "demo.csv").write_text(
        f"date,url,status,sha256,size_bytes\n2024-01-02,u,200,{hashlib.sha256(good).hexdigest()},10\n"
        f"2024-01-03,u,200,{hashlib.sha256(b'other').hexdigest()},5\n"
    )
    dataset = DatasetFiles("demo", lambda d: f"demo/{d}", lambda d: f"{d}.zip", date(2024, 1, 1))
    cache = InputCache(tmp_path / "cache", lambda path: good, manifests)
    with pytest.raises(HashMismatch):
        cache.fetch(dataset, log=lambda line: None)
    assert cache.read(dataset, date(2024, 1, 2)) == ("2024-01-02.zip", good)
    assert cache.read(dataset, date(2024, 1, 3)) is None
