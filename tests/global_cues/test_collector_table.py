"""Story A17: a failed download or unreadable file writes nothing and is named; every saved copy is logged; the table
is append-only (a held value is never rewritten, a late value never inserted, both logged as revisions); `live` only
when seen before the next NSE open."""

from datetime import date, datetime

from fno.global_cues.collector import CueCollector
from fno.global_cues.snapshot_log import SnapshotLog
from fno.global_cues.table import provenance
from fno.models import IST
from fno.storage.raw_store import LocalFolderStore
from tests.global_cues.fakes import REFUSED, FakeSource, csv_table, fake_file

SEEN = datetime(2026, 10, 15, 6, 15, tzinfo=IST)


def next_day(day: date) -> date:
    return date.fromordinal(day.toordinal() + 1)


def collector(tmp_path, clock=lambda: SEEN):
    return CueCollector(None, LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log"), clock)


def test_every_file_is_archived_under_its_fetch_time_and_logged(tmp_path):
    source = FakeSource({"a.csv": fake_file(("2026-10-13", 1.5), ("2026-10-14", 2.0))})
    result = collector(tmp_path).collect(source, date(2026, 10, 14), date(2026, 10, 14))
    assert not result.failure and [v.value.value_date for v in result.values] == [date(2026, 10, 14)]  # in range
    path = "test/cues/fake/2026/10/15/061500_a.csv"
    assert LocalFolderStore(tmp_path / "raw").get(path) == fake_file(("2026-10-13", 1.5), ("2026-10-14", 2.0))
    assert SnapshotLog(tmp_path / "log").paths_by_sha256("fake") == {result.values[0].source_sha256: path}


def test_one_failed_download_or_unreadable_file_writes_nothing_and_is_named(tmp_path):
    good = fake_file(("2026-10-14", 2.0))
    for broken, reason in ((REFUSED, "download failed"), (b"<html>error</html>", "not the publisher's file")):
        source = FakeSource({"a.csv": good, "b.csv": broken})
        result = collector(tmp_path).collect(source, date(2026, 1, 1), SEEN.date())
        assert result.failure.startswith(reason) and result.values == []
    assert not (tmp_path / "raw").exists() and not (tmp_path / "log").exists()


def table_after(tmp_path, *runs):
    table = csv_table(tmp_path / "tables", "fake", next_day)
    for seen, rows in runs:
        result = collector(tmp_path, clock=lambda seen=seen: seen).collect(
            FakeSource({"a.csv": fake_file(*rows)}), date(2026, 1, 1), date(2026, 12, 31)
        )
        table.merge(result.values, result.fetched_at)
    return table


def test_a_held_value_is_never_rewritten_and_a_late_value_never_inserted(tmp_path):
    first = (SEEN, [("2026-10-12", 1.0), ("2026-10-14", 2.0)])
    table = table_after(tmp_path, first)
    before = table.log.path.read_bytes()
    later = datetime(2026, 10, 16, 6, 0, tzinfo=IST)
    table = table_after(tmp_path, (later, [("2026-10-12", 1.1), ("2026-10-13", 1.5), ("2026-10-14", 2.0)]))
    assert table.log.path.read_bytes() == before  # nothing changed in the table
    revisions = (tmp_path / "tables" / "revisions.csv").read_text().splitlines()
    assert revisions[1].startswith("fake,2026-10-12,changed,1.0,1.1,")
    assert revisions[2].startswith("fake,2026-10-13,late,,1.5,")
    table_after(tmp_path, (datetime(2026, 10, 17, 6, 0, tzinfo=IST), [("2026-10-12", 1.1), ("2026-10-13", 1.5)]))
    assert len((tmp_path / "tables" / "revisions.csv").read_text().splitlines()) == 3  # never logged twice


def test_new_dates_are_appended_and_old_bytes_stay_a_prefix(tmp_path):
    table = table_after(tmp_path, (SEEN, [("2026-10-13", 1.0)]))
    before = table.log.path.read_bytes()
    later = datetime(2026, 10, 16, 6, 0, tzinfo=IST)
    table = table_after(tmp_path, (later, [("2026-10-13", 1.0), ("2026-10-14", 2.0)]))
    assert (
        table.log.path.read_bytes().startswith(before) and [r["value_date"] for r in table.rows()][-1] == "2026-10-14"
    )


def test_live_only_when_seen_before_the_first_nse_open_after_the_value_date():
    friday, monday = date(2026, 10, 9), date(2026, 10, 12)
    after = {friday: monday}.get
    assert provenance(friday, datetime(2026, 10, 12, 9, 14, tzinfo=IST), after) == "live"
    assert provenance(friday, datetime(2026, 10, 12, 9, 15, tzinfo=IST), after) == "backfilled"
    assert provenance(date(2007, 1, 3), SEEN, next_day) == "backfilled"
