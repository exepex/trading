"""A20a's 06:00 IST slot (orchestrator, 25 Oct 2026, for A14c part 2's 14:05 lot check): an earlier run keeps every
rule. The lots are filed under the run's own IST date; a later run the same day keeps the first copy and writes
nothing twice; at 06:00 the ban list on NSE is the run day's own session's list, filed under that date."""

from datetime import UTC, date, datetime
from pathlib import Path

from fno.models import IST
from fno.storage.content_checks import VALIDATORS
from fno.storage.raw_store import LocalFolderStore
from fno.storage.snapshot_source import FoBanListSource, FoLotSizeSource
from fno.storage.snapshot_taker import ALREADY, TAKEN, SnapshotTaker

from .test_job import ban_for, ban_taker

LOTS = (Path(__file__).parents[1] / "fixtures" / "nse" / "fo_masters" / "fo_mktlots_16102026.csv").read_bytes()
MONDAY = date(2026, 10, 26)


class Serving:
    """NSE's fixed-name file as served now; `data` may change between runs."""

    FILENAME, path_for = FoLotSizeSource.FILENAME, FoLotSizeSource.path_for

    def __init__(self, data: bytes):
        self.data = data

    def fetch(self, path):
        return self.data


def test_the_06_00_slot_runs_on_the_ist_day_it_files_under():
    """00:30 UTC is 06:00 IST the same date, so `now_ist().date()` (the CLI's day) is the session's own date."""
    fired = datetime(2026, 10, 26, 0, 30, tzinfo=UTC)
    assert fired.astimezone(IST).date() == fired.date() == MONDAY
    assert fired.astimezone(IST).strftime("%H:%M") == "06:00"


def test_the_lots_are_filed_under_the_run_day_and_a_later_run_writes_nothing_twice(tmp_path):
    store, source = LocalFolderStore(tmp_path), Serving(LOTS)
    taker = SnapshotTaker(store, source, VALIDATORS[FoLotSizeSource])
    path = FoLotSizeSource.path_for(MONDAY)
    assert path == "nse/derivatives/fo-lot-sizes/2026/10/26/fo_mktlots.csv"
    assert taker.take(MONDAY) == TAKEN.format(path=path, size=len(LOTS))  # the 06:00 run
    source.data = LOTS.replace(b"NIFTY", b"NIFTX", 1)  # even if NSE's copy changed by the 07:45 run
    assert taker.take(MONDAY) == ALREADY.format(path=path)
    assert store.get(path) == LOTS  # the first copy is the day's, never replaced
    assert [p.name for p in tmp_path.rglob("*") if p.is_file()] == ["fo_mktlots.csv"]


def test_at_06_00_the_ban_list_is_today_s_and_a_later_run_keeps_it(tmp_path):
    """NSE writes the session's list about 18:12 IST the evening before, so at 06:00 it names the run day."""
    store = LocalFolderStore(tmp_path)
    ban_taker(store, ban_for(MONDAY)).take(MONDAY)
    assert store.get(FoBanListSource.path_for(MONDAY)) == ban_for(MONDAY)
    ban_taker(store, ban_for(MONDAY)).take(MONDAY)  # the 07:45 run
    assert [p.name for p in tmp_path.rglob("*") if p.is_file()] == ["fo_secban.csv"]
