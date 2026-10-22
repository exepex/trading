"""Story A17, owner decision a927390: the S&P 500 and Nasdaq 100 closes are kept in Drive only (write-once parts),
downloaded at most once a day, and the four copies already in Drive are adopted at their own fetch time. All index
values here are made up (fake), never real ones."""

from datetime import date, datetime

import pytest

from fno.global_cues.check_files import GAPS_FILE, CueChecks
from fno.global_cues.collection import SourcedValue
from fno.global_cues.collector import CueCollector
from fno.global_cues.job import GlobalCueJob
from fno.global_cues.other_sources import FbilUsdInrSource
from fno.global_cues.snapshot_log import SnapshotLog
from fno.global_cues.table import CueTable
from fno.global_cues.us_index_sources import CboeSp500Source, NasdaqNdxSource
from fno.global_cues.verify import CueTableVerifier
from fno.models import IST
from fno.storage.raw_store import LocalFolderStore
from fno.storage.row_log import DrivePartsRowLog, DriveSnapshots
from tests.global_cues.fakes import FakeCreationTimes, cboe, fbil, nasdaq

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
    assert later.skipped.startswith("no download: today's copy of 06:14:45 IST read again") and source.downloads == 1
    assert [v.value.value for v in later.values] == [1000.5, 1001.25]  # the same copy, its first_seen time kept
    assert later.fetched_at == SEEN
    source.data = cboe(*FAKE, ("2026-10-15", 1002.0))
    next_day = collect.collect(source, date(2026, 1, 1), date(2026, 12, 31))
    assert not next_day.skipped and not next_day.failure and source.downloads == 2


def test_a_copy_already_in_drive_is_adopted_at_its_own_fetch_time(tmp_path):
    raw, log = LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log")
    raw.put(COPY, cboe(*FAKE))
    table = drive_table(LocalFolderStore(tmp_path / "derived"))
    checks = CueChecks({"sp500": table}, tmp_path / "checks", {"sp500": DriveSnapshots(raw, "checks", lambda: SEEN)})
    job = GlobalCueJob(CueCollector(None, raw, log, None, FakeCreationTimes()), {"sp500": table}, checks)
    lines, ok = job.adopt(CboeSp500Source(), COPY, date(2007, 1, 1), date(2026, 10, 15))
    assert ok and lines[0].startswith("sp500: 2 dates added")
    assert {r["first_seen_at"] for r in table.rows()} == {SEEN.isoformat()}
    assert log.paths_by_sha256("sp500") and list(log.paths_by_sha256("sp500").values()) == [COPY]
    again, _ = job.adopt(CboeSp500Source(), COPY, date(2007, 1, 1), date(2026, 10, 15))
    assert again[0].startswith("sp500: 0 dates added")
    assert len(log.path_for("sp500").read_text().splitlines()) == 2  # header and one row: never logged twice


def test_a_copy_that_matches_no_request_or_is_missing_is_refused(tmp_path):
    raw = LocalFolderStore(tmp_path / "raw")
    copies = CueCollector(None, raw, SnapshotLog(tmp_path / "log"), None, FakeCreationTimes()).copies
    other = "nasdaq/indices/ndx-history/2026/10/15/061722_ndx-history_20260912_20261015.json"
    ndx, full, month = (
        NasdaqNdxSource(),
        (date(2007, 1, 1), date(2026, 10, 15)),
        (date(2026, 9, 12), date(2026, 10, 15)),
    )
    assert "no request named" in copies.adopt(ndx, other, *full).failure
    assert "is not in the archive" in copies.adopt(ndx, other, *month).failure
    assert "not a copy path" in copies.adopt(ndx, "nasdaq/x.json", *month).failure
    elsewhere = "cboe/indices/spx-history/2026/10/15/061722_ndx-history_20260912_20261015.json"  # name fits, folder not
    assert "not nasdaq100's dataset" in copies.adopt(ndx, elsewhere, *month).failure


def test_a_private_cues_gaps_go_to_drive_never_to_the_repositorys_checks(tmp_path):
    drive = LocalFolderStore(tmp_path / "derived")
    table = drive_table(drive)
    collect = CueCollector(None, LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log"), lambda: SEEN)
    gapped = FakeCboe(cboe(("2026-10-09", 999.0), ("2026-10-14", 1001.25)))
    table.merge(collect.collect(gapped, date(2026, 1, 1), date(2026, 12, 31)).values, SEEN)
    times = iter([SEEN, datetime(2026, 10, 15, 7, 0, tzinfo=IST)])
    snapshots = DriveSnapshots(drive, "global-cues/sp500/checks", lambda: next(times))
    lines = CueChecks({"sp500": table}, tmp_path / "checks", {"sp500": snapshots}).write()
    assert "sp500 weekday_without_value 2" in lines[0]  # Monday 12 and Tuesday 13 Oct
    assert "sp500" not in (tmp_path / "checks" / GAPS_FILE).read_text()
    assert [r["date"] for r in snapshots.latest()] == ["2026-10-12", "2026-10-13"]
    CueChecks(
        {"sp500": drive_table(LocalFolderStore(tmp_path / "other"))}, tmp_path / "checks", {"sp500": snapshots}
    ).write()
    assert snapshots.latest() == []  # the newest snapshot is current: cleared gaps are gone from it


def test_a_second_copy_of_the_same_bytes_is_logged_too_and_adds_no_row(tmp_path):
    raw, log = LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log")
    second = COPY.replace("061445", "061718")
    raw.put(COPY, cboe(*FAKE))
    raw.put(second, cboe(*FAKE))
    table = drive_table(LocalFolderStore(tmp_path / "derived"))
    job = GlobalCueJob(
        CueCollector(None, raw, log, None, FakeCreationTimes()), {"sp500": table}, CueChecks({}, tmp_path / "checks")
    )
    job.adopt(CboeSp500Source(), COPY, date(2007, 1, 1), date(2026, 10, 15))
    lines, _ = job.adopt(CboeSp500Source(), second, date(2007, 1, 1), date(2026, 10, 15))
    assert log.paths("sp500") == {COPY, second} and lines[0].startswith("sp500: 0 dates added")


def test_an_unfinished_close_in_a_file_read_during_the_us_session_never_becomes_a_row(tmp_path):
    during = datetime(2026, 10, 14, 21, 0, tzinfo=IST)  # 11:30 New York on 14 Oct: the session is open
    collect = CueCollector(None, LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log"), lambda: during)
    result = collect.collect(FakeCboe(), date(2026, 1, 1), date(2026, 12, 31))
    assert [v.value.value_date for v in result.values] == [date(2026, 10, 13)]  # 14 Oct's price so far is dropped


def test_a_run_whose_table_write_failed_finishes_the_same_day_from_its_copy(tmp_path):
    raw, log = LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log")
    source = FakeCboe()
    first = CueCollector(None, raw, log, lambda: SEEN).collect(source, date(2026, 1, 1), date(2026, 12, 31))
    assert first.values  # archived and logged; suppose the table write then failed and nothing was merged
    rerun = CueCollector(None, raw, log, lambda: datetime(2026, 10, 15, 11, 0, tzinfo=IST))
    table = drive_table(LocalFolderStore(tmp_path / "derived"))
    result = rerun.collect(source, date(2026, 1, 1), date(2026, 12, 31))
    table.merge(result.values, result.fetched_at)
    assert source.downloads == 1 and {r["first_seen_at"] for r in table.rows()} == {SEEN.isoformat()}


def test_verify_never_prints_a_private_value(tmp_path):
    raw, log = LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log")
    values = CueCollector(None, raw, log, lambda: SEEN).collect(FakeCboe(), date(2026, 1, 1), date(2026, 12, 31)).values
    table = drive_table(LocalFolderStore(tmp_path / "derived"))
    table.merge(values, SEEN)
    planted = dict(table.rows()[0], value="1234.5")
    (problem,) = CueTableVerifier(raw, log, lambda d: d).problems(CboeSp500Source(), [planted])
    assert problem == "sp500 2026-10-13: values differ (private cue: values never printed)"
    assert "1234.5" not in problem and "1000.5" not in problem


def test_a_checks_failure_never_hides_the_cue_lines(tmp_path):
    class BrokenChecks:
        def write(self):
            raise RuntimeError("Drive refused the gaps snapshot")

    table = drive_table(LocalFolderStore(tmp_path / "derived"))
    collect = CueCollector(None, LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log"), lambda: SEEN)
    lines, ok = GlobalCueJob(collect, {"sp500": table}, BrokenChecks()).run([FakeCboe()], None, date(2026, 10, 15))
    assert not ok and lines[0].startswith("sp500: 2 dates added")
    assert lines[1] == "checks FAILED (RuntimeError): Drive refused the gaps snapshot"


def test_fbil_is_private_and_its_table_and_revisions_go_to_drive_never_to_the_repository(tmp_path, monkeypatch):
    """Story A17d: FBIL's USD/INR rows live in Drive's derived area, like the US closes (made-up rates)."""
    from fno.global_cues import wiring

    drive = LocalFolderStore(tmp_path / "drive")
    monkeypatch.setattr(wiring.storage, "build_owner_drive", lambda env: drive)
    assert FbilUsdInrSource().private and not FbilUsdInrSource().once_a_day
    assert "usdinr_fbil" not in wiring.build_tables(include_private=False)
    table = wiring.build_tables()["usdinr_fbil"]
    for rate in (91.2345, 91.5):  # the second is a revision
        table.merge([SourcedValue(v, "a" * 64) for v in FbilUsdInrSource().parse(fbil(("2026-10-07", rate)))], SEEN)
    held = {p.relative_to(tmp_path / "drive").parts[:4] for p in (tmp_path / "drive").rglob("*.csv")}
    assert held == {
        ("derived", "global-cues", "usdinr_fbil", "rows"),
        ("derived", "global-cues", "usdinr_fbil", "revisions"),
    }
    assert [r["value"] for r in table.rows()] == ["91.2345"]
