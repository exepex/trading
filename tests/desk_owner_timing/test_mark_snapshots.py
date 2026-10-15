"""E8 rule 3 and acceptance 3-4: the due mark's A16 copy (ledger-named, hash checked) read through A4's own quote
rule, the A4 stand-in inside the 2-minute window, and never a neighbouring mark."""

from __future__ import annotations

import hashlib
from datetime import date, timedelta

import pytest

from fno.desk.owner_timing.mark_snapshots import CaptureStandIn, FirstAvailable, IntradayMarkSnapshots
from fno.desk.snapshot import RecordedExecutionSnapshots, SnapshotError
from fno.intraday.document import CallRecord, SnapshotDocument, utc_text
from fno.intraday.ledger import FIELDS, SlotLedger
from tests.desk.builders import DictStore, fly_rows, write_snapshot
from tests.desk_owner_timing.fakes import ist

FRI = date(2026, 10, 16)
MARK = ist(FRI, 10, 15)
EXPIRY = "2026-10-27"
PATH = "groww/derivatives/intraday-snapshots/2026/10/16/nifty_20261016_1015_abcd.json.gz"


def quote(strike, kind, bid=100.0, ask=101.0, traded=MARK, sent=MARK + timedelta(seconds=5)):
    payload = {"bid_price": bid, "offer_price": ask, "bid_quantity": 650, "offer_quantity": 650}
    if traded is not None:
        payload["last_trade_time"] = int(traded.timestamp())
    meta = {"expiry": EXPIRY, "strike": strike, "type": kind, "symbol": f"NIFTY27OCT26{strike}{kind}"}
    return CallRecord(f"quote {strike}{kind}", sent, sent + timedelta(seconds=1), payload, "", meta)


def document(quotes, mark=MARK) -> bytes:
    index = CallRecord("index", mark, mark + timedelta(seconds=1), {"last_price": 25000})
    doc = SnapshotDocument("groww", "NIFTY", FRI, mark, index, 25000.0, mark, quotes=quotes)
    doc.finished_at = mark + timedelta(seconds=50)
    return doc.to_bytes()


def recorded(tmp_path, data: bytes, status="good", sha=None):
    store, ledger = DictStore(), SlotLedger(tmp_path)
    store.put(PATH, data)
    row = {name: "" for name in FIELDS} | {
        "session": FRI.isoformat(), "mark": utc_text(MARK), "status": status, "raw_path": PATH,
        "raw_sha256": sha or hashlib.sha256(data).hexdigest(),
    }  # fmt: skip
    ledger.append(FRI, [row])
    return IntradayMarkSnapshots(store, ledger)


def test_the_marks_copy_becomes_an_execution_snapshot(tmp_path):
    snapshot = recorded(tmp_path, document([quote(25000, "CE")])).at(FRI, MARK)
    found = snapshot.quote(date(2026, 10, 27), 25000, "CE")
    assert (found.bid, found.ask, found.a4_problem) == (100.0, 101.0, "")
    assert snapshot.started_at == MARK and snapshot.complete


def test_a_changed_copy_is_refused(tmp_path):
    with pytest.raises(SnapshotError, match="ledger hash"):
        recorded(tmp_path, document([quote(25000, "CE")]), sha="0" * 64).at(FRI, MARK)


def test_a_late_copy_or_another_mark_is_never_used(tmp_path):
    late = recorded(tmp_path, document([quote(25000, "CE")]), status="late")
    assert late.at(FRI, MARK) is None
    assert late.at(FRI, MARK + timedelta(minutes=15)) is None  # no row for 10:30: no neighbouring mark


def test_a_quote_without_a_trade_that_session_is_not_valid(tmp_path):
    stale = quote(25000, "CE", traded=MARK - timedelta(days=1))
    found = recorded(tmp_path, document([stale])).at(FRI, MARK).quote(date(2026, 10, 27), 25000, "CE")
    assert found.a4_problem.startswith("no trade today")


def test_a_quote_requested_before_the_mark_is_dropped(tmp_path):
    early = quote(25000, "CE", sent=MARK - timedelta(seconds=30))
    assert recorded(tmp_path, document([early])).at(FRI, MARK).quote(date(2026, 10, 27), 25000, "CE") is None


def test_an_a4_capture_inside_the_window_stands_in(tmp_path):
    store, mark = DictStore(), ist(FRI, 15, 15)
    write_snapshot(
        store,
        "nifty_20261016_151530",
        fly_rows(),
        ist(
            FRI,
            15,
            15,
        ),
        mark + timedelta(seconds=40),
        day=FRI,
    )
    write_snapshot(store, "nifty_20261016_151830", fly_rows(), mark + timedelta(minutes=3), mark + timedelta(minutes=4),
                   day=FRI)  # fmt: skip
    names = lambda day: ["nifty_20261016_151830.meta.json", "nifty_20261016_151530.meta.json"]  # noqa: E731
    stand_in = CaptureStandIn(RecordedExecutionSnapshots(store), names)
    empty_a16 = IntradayMarkSnapshots(DictStore(), SlotLedger(tmp_path))
    assert FirstAvailable(empty_a16, stand_in).at(FRI, mark).snapshot_id == "nifty_20261016_151530"
    assert stand_in.at(FRI, ist(FRI, 15, 30)) is None  # 15:18 is outside 15:30's window too
