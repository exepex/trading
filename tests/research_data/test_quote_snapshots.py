"""Reading A4's 3 pm snapshots back for live features (story B7), on A4's own golden fixtures."""

from datetime import date, datetime
from pathlib import Path

from fno.research_data.quote_snapshots import LiveQuote, RecordedSnapshots
from fno.storage.raw_store import LocalFolderStore

GOLDEN = Path(__file__).resolve().parents[1] / "fixtures" / "quote_recorder_golden"
DAY = date(2026, 10, 13)


def test_the_canonical_snapshot_is_read_with_capture_time_spot_and_quotes():
    snap = RecordedSnapshots(LocalFolderStore(GOLDEN / "normal")).snapshot(DAY)
    assert snap.finished_at == datetime(2026, 10, 13, 14, 55, 28) and snap.spot == 22000.0
    assert snap.vix is None  # A4 records no India VIX
    assert snap.expiries == [date(2026, 10, 27), date(2026, 11, 24)] and len(snap.quotes) == 12
    assert snap.quotes[0] == LiveQuote(date(2026, 10, 27), 21000.0, "CE", 10.0, 11.0, True, "N21000CE")


def test_a_none_day_has_no_snapshot():
    store = RecordedSnapshots(LocalFolderStore(GOLDEN / "none"))
    assert store.snapshot(DAY) is None and store.snapshots([DAY, date(2026, 10, 14)]) == {}


def test_a_mid_needs_a_valid_two_sided_quote():
    assert LiveQuote(DAY, 1.0, "CE", 10.0, 11.0, True).mid == 10.5
    assert LiveQuote(DAY, 1.0, "CE", 10.0, 11.0, False).mid is None
    assert LiveQuote(DAY, 1.0, "CE", None, 11.0, True).mid is None
    assert LiveQuote(DAY, 1.0, "CE", 12.0, 11.0, True).mid is None  # crossed book
