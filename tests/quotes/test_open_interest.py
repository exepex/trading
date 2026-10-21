"""Story A4f: every 3 pm snapshot row carries the chain leg's open interest as its last column; the readers of the
snapshot read a file with it unchanged."""

import csv
import io
from datetime import date, datetime

from fno.models import IST, OptionChain, OptionQuote, QuoteBook
from fno.quotes.book_fetch import Fetched
from fno.quotes.recorder import QuoteSnapshotRecorder
from fno.quotes.report import canonical_snapshots, spread_report
from fno.quotes.snapshot_rows import COLUMNS, snapshot_row
from fno.research_data.quote_snapshots import RecordedSnapshots
from fno.storage.raw_store import LocalFolderStore
from tests.quotes.test_quote_recorder import Clock, FakeProvider

DAY = date(2026, 10, 13)
TRADED = datetime(2026, 10, 13, 14, 58, tzinfo=IST)
SENT, RECEIVED = datetime(2026, 10, 13, 14, 55, 1, tzinfo=IST), datetime(2026, 10, 13, 14, 55, 2, tzinfo=IST)


def _chain(oi):
    quotes = {(22000.0, "CE"): OptionQuote(22000.0, "CE", 10.0, oi=oi, symbol="N22000CE")}
    return OptionChain("NIFTY", 22000.0, date(2026, 10, 27), TRADED, 65, quotes)


def _row(chain, strike=22000.0, kind="CE"):
    book = QuoteBook(f"N{strike:g}{kind}", 10.0, 11.0, 65, 130, 10.5, TRADED, "fields", "h")
    return snapshot_row("nifty_x", "fake", Fetched(strike, kind, SENT, RECEIVED, book, None), chain, DAY)


def test_open_interest_is_the_last_column_and_the_chain_leg_s_value():
    assert COLUMNS[-1] == "open_interest"
    assert _row(_chain(12345675.0))["open_interest"] == "12345675"  # in full: NIFTY open interest runs into crores


def test_zero_open_interest_is_written_as_zero_and_a_leg_the_chain_lacks_gives_an_empty_cell():
    assert _row(_chain(0.0))["open_interest"] == "0"
    assert _row(_chain(5.0), strike=22050.0)["open_interest"] == ""


def test_the_readers_read_a_recorded_file_with_the_column(tmp_path):
    clock = Clock(datetime(2026, 10, 13, 14, 55, tzinfo=IST))
    recorder = QuoteSnapshotRecorder(FakeProvider(), LocalFolderStore(tmp_path), clock.now, clock.sleep)
    result = recorder.record()
    store = LocalFolderStore(tmp_path)
    [text] = canonical_snapshots(tmp_path, store)
    assert csv.DictReader(io.StringIO(text)).fieldnames[-1] == "open_interest" and spread_report([text])
    snapshot = RecordedSnapshots(store).snapshot(DAY)
    assert snapshot is not None and len(snapshot.quotes) == result.rows
