"""Story A17, owner decision a927390: the S&P 500 and Nasdaq 100 closes are kept in Drive only (write-once parts),
downloaded at most once a day, and the four copies already in Drive are adopted at their own fetch time. All index
values here are made up (fake), never real ones."""

from datetime import date, datetime

import pytest

from fno.global_cues.check_files import GAPS_FILE, CueChecks
from fno.global_cues.collector import CueCollector
from fno.global_cues.job import GlobalCueJob
from fno.global_cues.row_log import DrivePartsRowLog
from fno.global_cues.snapshot_log import SnapshotLog
from fno.global_cues.table import CueTable
from fno.global_cues.us_index_sources import CboeSp500Source, NasdaqNdxSource
from fno.models import IST
from fno.storage.raw_store import LocalFolderStore
from tests.global_cues.fakes import cboe, nasdaq

FAKE = [("2026-10-13", 1000.5), ("2026-10-14", 1001.25)]  # fake levels
SEEN = datetime(2026, 10, 15, 6, 14, 45, tzinfo=IST)
COPY = "cboe/indices/spx-history/2026/10/15/061445_spx-history.json"


class FakeCboe(CboeSp500Source):
    def __init__(self, data=None):
        self.data, self.downloads = data or cboe(*FAKE), 0

    def download(self, session, request):
        self.downloads += 1
        return self.data


def drive_table(drive, cue="sp500"):
    clock = iter(datetime(2026, 10, 15, 7, m, tzinfo=IST) for m in range(60)).__next__
    rows = DrivePartsRowLog(drive, f"global-cues/{cue}/rows", clock)
    return CueTable(cue, rows, DrivePartsRowLog(drive, f"global-cues/{cue}/revisions", clock), lambda d: d)


def test_cboe_and_nasdaq_layouts_are_read_and_a_cut_nasdaq_answer_refused():
    assert [v.value for v in CboeSp500Source().parse(cboe(*FAKE))] == [1000.5, 1001.25]
    rows = [("10/14/2026", "2,001.50"), ("10/13/2026", "2,000.00")]
    assert [v.value for v in NasdaqNdxSource().parse(nasdaq(rows))] == [2000.0, 2001.5]
    with pytest.raises(ValueError, match="the answer was cut"):
        NasdaqNdxSource().parse(nasdaq(rows, total=3))
    assert CboeSp500Source().private and CboeSp500Source().once_a_day and NasdaqNdxSource().private


def test_a_drive_table_is_write_once_parts_and_never_rewritten(tmp_path):
    drive = LocalFolderStore(tmp_path / "derived")
    table = drive_table(drive)
    collect = CueCollector(None, LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log"), lambda: SEEN)
    values = collect.collect(FakeCboe(), date(2026, 1, 1), date(2026, 12, 31)).values
    table.merge(values[:1], SEEN)
    first = sorted(drive.checksums("global-cues/sp500/rows").items())
    table.merge(values, SEEN)
    parts = sorted(drive.checksums("global-cues/sp500/rows").items())
    assert len(parts) == 2 and parts[0] == first[0]  # the first part is unchanged; the new row is a new part
    assert [r["value_date"] for r in table.rows()] == ["2026-10-13", "2026-10-14"]
    table.merge(values, SEEN)
    assert len(drive.checksums("global-cues/sp500/rows")) == 2  # nothing new: no empty part either


def test_at_most_one_download_a_day(tmp_path):
    source = FakeCboe()
    day_two = datetime(2026, 10, 16, 6, 0, tzinfo=IST)
    clock = iter([SEEN, SEEN, datetime(2026, 10, 15, 20, 0, tzinfo=IST), day_two, day_two])  # a start and an end each
    collect = CueCollector(None, LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log"), lambda: next(clock))
    assert not collect.collect(source, date(2026, 1, 1), date(2026, 12, 31)).skipped
    later = collect.collect(source, date(2026, 1, 1), date(2026, 12, 31))
    assert later.skipped.startswith("already downloaded on 2026-10-15") and source.downloads == 1
    source.data = cboe(*FAKE, ("2026-10-15", 1002.0))
    next_day = collect.collect(source, date(2026, 1, 1), date(2026, 12, 31))
    assert not next_day.skipped and not next_day.failure and source.downloads == 2


def test_a_copy_already_in_drive_is_adopted_at_its_own_fetch_time(tmp_path):
    raw, log = LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log")
    raw.put(COPY, cboe(*FAKE))
    table = drive_table(LocalFolderStore(tmp_path / "derived"))
    checks = CueChecks({"sp500": table}, tmp_path / "checks", {"sp500": table.revision_log})
    job = GlobalCueJob(CueCollector(None, raw, log, None), {"sp500": table}, checks)
    lines, ok = job.adopt(CboeSp500Source(), COPY, date(2007, 1, 1), date(2026, 10, 15))
    assert ok and lines[0].startswith("sp500: 2 dates added")
    assert {r["first_seen_at"] for r in table.rows()} == {SEEN.isoformat()}
    assert log.paths_by_sha256("sp500") and list(log.paths_by_sha256("sp500").values()) == [COPY]
    again, _ = job.adopt(CboeSp500Source(), COPY, date(2007, 1, 1), date(2026, 10, 15))
    assert again[0].startswith("sp500: 0 dates added") and len(log.fetched_by_sha256("sp500")) == 1


def test_a_copy_that_matches_no_request_or_is_missing_is_refused(tmp_path):
    raw = LocalFolderStore(tmp_path / "raw")
    collect = CueCollector(None, raw, SnapshotLog(tmp_path / "log"), None)
    other = "nasdaq/indices/ndx-history/2026/10/15/061722_ndx-history_20260912_20261015.json"
    assert "no request named" in collect.adopt(NasdaqNdxSource(), other, date(2007, 1, 1), date(2026, 10, 15)).failure
    assert "not archived" in collect.adopt(NasdaqNdxSource(), other, date(2026, 9, 12), date(2026, 10, 15)).failure


def test_a_private_cues_gaps_go_to_drive_never_to_the_repositorys_checks(tmp_path):
    drive = LocalFolderStore(tmp_path / "derived")
    table = drive_table(drive)
    collect = CueCollector(None, LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log"), lambda: SEEN)
    gapped = FakeCboe(cboe(("2026-10-09", 999.0), ("2026-10-14", 1001.25)))
    table.merge(collect.collect(gapped, date(2026, 1, 1), date(2026, 12, 31)).values, SEEN)
    gaps_log = DrivePartsRowLog(drive, "global-cues/sp500/checks", lambda: SEEN)
    lines = CueChecks({"sp500": table}, tmp_path / "checks", {"sp500": gaps_log}).write()
    assert "sp500 weekday_without_value 2" in lines[0]  # Monday 12 and Tuesday 13 Oct
    assert "sp500" not in (tmp_path / "checks" / GAPS_FILE).read_text()
    assert [r["date"] for r in gaps_log.rows()] == ["2026-10-12", "2026-10-13"]


def test_a_second_copy_of_the_same_bytes_is_logged_too_and_adds_no_row(tmp_path):
    raw, log = LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log")
    second = COPY.replace("061445", "061718")
    raw.put(COPY, cboe(*FAKE))
    raw.put(second, cboe(*FAKE))
    table = drive_table(LocalFolderStore(tmp_path / "derived"))
    job = GlobalCueJob(CueCollector(None, raw, log, None), {"sp500": table}, CueChecks({}, tmp_path / "checks"))
    job.adopt(CboeSp500Source(), COPY, date(2007, 1, 1), date(2026, 10, 15))
    lines, _ = job.adopt(CboeSp500Source(), second, date(2007, 1, 1), date(2026, 10, 15))
    assert log.paths("sp500") == {COPY, second} and lines[0].startswith("sp500: 0 dates added")
