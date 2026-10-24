"""DRY1 row c4 (23 Oct 2026): `verify` failed every FBIL row because A17d adopted copies the fill had already logged.
Adopt stamps the copy path's whole second, the log keeps the fill's microseconds; verify now compares the two at the
path's precision, and a row really seen before its copy's second still fails."""

from datetime import UTC, date, datetime

import pytest

from fno.global_cues.collector import CueCollector
from fno.global_cues.snapshot_log import SnapshotLog
from fno.global_cues.verify import CueTableVerifier
from fno.models import IST
from fno.storage.raw_store import LocalFolderStore
from tests.global_cues.fakes import FakeCreationTimes, FakeSource, csv_table, fake_file

FETCHED = datetime(2026, 10, 15, 6, 16, 31, 10317, tzinfo=IST)  # FBIL's fill: 06:16:31.010317, its path 061631
START, END = date(2026, 1, 1), date(2026, 12, 31)
GOOD = fake_file(("2026-10-13", 1.0), ("2026-10-14", 2.0))


@pytest.fixture
def adopted(tmp_path):
    """The A17d path: a fill logs its copy at microseconds, then an adopt of that same copy fills the table."""
    store, log, source = LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log"), FakeSource({"a.csv": GOOD})
    collector = CueCollector(None, store, log, lambda: FETCHED, FakeCreationTimes())
    collector.collect(source, START, END)
    (path,) = log.paths(source.cue)
    collection = collector.copies.adopt(source, path, START, END)
    table = csv_table(tmp_path / "tables", source.cue, lambda d: d)
    table.merge(collection.values, collection.fetched_at)
    return CueTableVerifier(store, log, lambda d: d), source, table.rows()


def test_an_adopted_copy_already_logged_by_its_fill_verifies(adopted):
    verifier, source, rows = adopted
    assert {r["first_seen_at"] for r in rows} == {"2026-10-15T06:16:31+05:30"}  # the path's second, as on 15 Oct
    assert verifier.problems(source, rows) == []


@pytest.mark.parametrize("seen", ["2026-10-15T06:16:30+05:30", "2026-10-15T06:16:30.999999+05:30"])
def test_a_row_seen_before_its_copys_second_still_fails(adopted, seen):
    verifier, source, rows = adopted
    (problem,) = verifier.problems(source, [dict(rows[0], first_seen_at=seen)])
    assert "before its copy was fetched" in problem


@pytest.mark.parametrize(("utc", "fails"), [(datetime(2026, 10, 15, 0, 46, 30, tzinfo=UTC), True),
                                             (datetime(2026, 10, 15, 0, 46, 31, tzinfo=UTC), False)])  # fmt: skip
def test_a_first_seen_written_in_utc_is_compared_as_the_same_moment(adopted, utc, fails):
    verifier, source, rows = adopted  # 00:46:31 UTC is 06:16:31 IST, the copy's own second
    assert bool(verifier.problems(source, [dict(rows[0], first_seen_at=utc.isoformat())])) is fails
