"""Protocol sections 3, 8 and 9 on hand-made inputs: the seal at load, the lot read from a day's F&O rows (UDiFF's
board lot first, else R2's derived lot; monthly options only), and the SPAN file's point-in-time checks."""

import hashlib
from datetime import date, datetime, timedelta, timezone

import edge1study.margin as margin
import pytest
from edge1study.day_files import derived_lot, rows_of
from edge1study.inputs import rows_through
from edge1study.margin import BEFORE_SPAN, NO_FILE, NOT_FIRST_COPY, TOO_LATE, span_on

DAY, MONTHLY, WEEKLY = date(2022, 3, 3), date(2022, 3, 31), date(2022, 3, 10)
IST = timezone(timedelta(hours=5, minutes=30))


def record(kind, expiry, strike="", option="", lot="", turnover="0", volume="0", settle="0"):
    return {"TckrSymb": "BANKNIFTY", "FinInstrmTp": kind, "XpryDt": expiry.isoformat(), "StrkPric": strike,
            "OptnTp": option, "ClsPric": "10", "SttlmPric": settle, "TtlTradgVol": volume, "OpnIntrst": "5",
            "NewBrdLotQty": lot, "TtlTrfVal": turnover}  # fmt: skip


def test_rows_after_the_seal_are_dropped_before_any_panel_is_built():
    class Row:
        def __init__(self, day):
            self.day = day

    rows = {"NIFTY": [Row(date(2023, 2, 14)), Row(date(2023, 2, 15))], "BANKNIFTY": [Row(date(2023, 3, 1))]}
    found = rows_through(rows, date(2023, 2, 14))
    assert [r.day for r in found["NIFTY"]] == [date(2023, 2, 14)] and found["BANKNIFTY"] == []


def test_derived_lot_is_turnover_over_contracts_times_settlement_rounded():
    assert derived_lot(25 * 40_000.0 * 10 + 30_000.0, 10, 40_000.0) == 25
    assert derived_lot(0.0, 10, 40_000.0) is None and derived_lot(1.0, 0, 40_000.0) is None


def test_the_board_lot_wins_and_the_derived_lot_fills_in_without_it():
    future = record("IDF", MONTHLY, turnover=str(25 * 40_000 * 4), volume="4", settle="40000")
    assert rows_of(DAY, [future], "BANKNIFTY", "legacy").lots == {MONTHLY: 25}
    assert rows_of(DAY, [record("IDF", MONTHLY, lot="15"), future], "BANKNIFTY", "udiff").lots == {MONTHLY: 15}


def test_only_monthly_options_of_the_symbol_are_kept():
    rows = [
        record("IDF", MONTHLY, settle="40000"),
        record("IDO", MONTHLY, "40000", "CE"),
        record("IDO", WEEKLY, "40000", "CE"),
        {**record("IDO", MONTHLY, "40000", "PE"), "TckrSymb": "NIFTY"},
    ]
    found = rows_of(DAY, rows, "BANKNIFTY", "legacy")
    assert [(q.expiry, q.kind) for q in found.options] == [(MONTHLY, "CE")]
    assert rows_of(DAY, rows, "BANKNIFTY", "legacy", with_options=False).options == ()


class Span:
    def __init__(self, created):
        self.created = created


@pytest.fixture
def span_at(monkeypatch):
    def at(hour, minute):
        monkeypatch.setattr(margin, "read_span_file", lambda *a, **k: Span(datetime(2022, 3, 3, hour, minute,
                                                                                     tzinfo=IST)))  # fmt: skip

    return at


def test_span_files_are_checked_point_in_time(span_at):
    data = b"span"
    sha = {DAY: hashlib.sha256(data).hexdigest()}
    span_at(8, 59)
    assert span_on(lambda d: ("f.zip", data), DAY, sha, "BANKNIFTY")[1] is None
    span_at(9, 0)
    assert span_on(lambda d: ("f.zip", data), DAY, sha, "BANKNIFTY") == (None, TOO_LATE)
    assert span_on(lambda d: ("f.zip", b"other"), DAY, sha, "BANKNIFTY") == (None, NOT_FIRST_COPY)
    assert span_on(lambda d: ("f.zip", None), DAY, sha, "BANKNIFTY") == (None, NO_FILE)
    assert span_on(lambda d: ("f.zip", data), date(2019, 12, 31), sha, "BANKNIFTY") == (None, BEFORE_SPAN)
