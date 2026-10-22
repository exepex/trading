"""Story A17b, criteria 3-5: the `live` label never uses a muhurat session as an open, adopt checks the store's own
creation time, and a once-a-day cue's attempts are logged (time and outcome only) and capped. Values are fake."""

import csv
from datetime import UTC, date, datetime, timedelta

import pytest

from fno.global_cues.archived_copies import ADOPT_WINDOW
from fno.global_cues.attempt_log import FIELDS, MAX_ATTEMPTS
from fno.global_cues.collector import ATTEMPTS_FOLDER, CueCollector
from fno.global_cues.snapshot_log import SnapshotLog
from fno.global_cues.table import BACKFILLED, LIVE, provenance
from fno.global_cues.us_index_sources import CboeSp500Source
from fno.global_cues.wiring import next_nse_session
from fno.models import IST
from fno.research_data.calendar import CsvSessionCalendar
from fno.storage.raw_store import LocalFolderStore
from fno.storage.row_log import TableFileBroken
from tests.global_cues.fakes import REFUSED, FakeCreationTimes, FakeSource, cboe, fake_file

SOURCE = "https://nsearchives.nseindia.com/content/circulars/example.pdf"
MUHURAT = CsvSessionCalendar(f"date,kind,description,source_url\n2024-11-01,muhurat,Diwali muhurat session,{SOURCE}\n")
COPY = "cboe/indices/spx-history/2026/10/15/061445_spx-history.json"
PATH_TIME = datetime(2026, 10, 15, 6, 14, 45, tzinfo=IST)
SPAN = (date(2007, 1, 1), date(2026, 10, 15))
FAKE = cboe(("2026-10-13", 1000.5), ("2026-10-14", 1001.25))  # fake levels


def test_the_first_open_after_a_value_skips_a_muhurat_session():
    after = next_nse_session(MUHURAT, MUHURAT.first)
    assert after(date(2024, 10, 31)) == date(2024, 11, 4)  # Friday 1 Nov is muhurat only: Monday is the open
    seen_on_muhurat_evening = datetime(2024, 11, 1, 19, 0, tzinfo=IST)
    assert provenance(date(2024, 10, 31), seen_on_muhurat_evening, after) == LIVE
    assert provenance(date(2024, 10, 31), datetime(2024, 11, 4, 9, 15, tzinfo=IST), after) == BACKFILLED
    assert after(date(2024, 10, 30)) == date(2024, 10, 31)  # an ordinary day is unchanged


class Times(FakeCreationTimes):
    def __init__(self, created):
        self.created = created

    def created_at(self, path):
        return self.created


def adopt(tmp_path, created):
    raw = LocalFolderStore(tmp_path / "raw")
    raw.put(COPY, FAKE)
    times = None if created == "no store" else Times(created)
    collector = CueCollector(None, raw, SnapshotLog(tmp_path / "log"), None, times)
    return collector.copies.adopt(CboeSp500Source(), COPY, *SPAN)


def test_adopt_takes_a_copy_created_within_ten_minutes_after_its_path_time(tmp_path):
    for n, created in enumerate((PATH_TIME, PATH_TIME + timedelta(seconds=9), PATH_TIME + ADOPT_WINDOW)):
        assert adopt(tmp_path / str(n), created).failure == "", created


def test_adopt_refuses_a_copy_created_before_or_too_long_after_and_names_both_times(tmp_path):
    early = adopt(tmp_path / "early", PATH_TIME - timedelta(seconds=1)).failure
    assert "created 2026-10-15T06:14:44+05:30" in early and "path time 2026-10-15T06:14:45+05:30" in early
    late = adopt(tmp_path / "late", PATH_TIME + ADOPT_WINDOW + timedelta(seconds=1)).failure
    assert "not within 0:10:00" in late
    assert not SnapshotLog(tmp_path / "late" / "log").paths("sp500")  # nothing logged


def test_adopt_refuses_when_the_store_cannot_give_the_creation_time(tmp_path):
    assert "cannot give its creation time" in adopt(tmp_path / "unknown", None).failure
    assert "cannot give its creation time" in adopt(tmp_path / "none", "no store").failure


class FlakyCboe(CboeSp500Source):
    def __init__(self, answers):
        self.answers, self.downloads = list(answers), 0

    def download(self, session, request):
        self.downloads += 1
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def collector(tmp_path, clock):
    return CueCollector(None, LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log"), clock)


def attempts(tmp_path):
    with open(tmp_path / "log" / ATTEMPTS_FOLDER / "sp500.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_a_third_failed_attempt_is_the_last_that_day(tmp_path):
    source = FlakyCboe([REFUSED, b"<html>busy</html>", REFUSED, FAKE])
    times = iter(datetime(2026, 10, 15, 6, m, tzinfo=IST) for m in range(10))
    collect = collector(tmp_path, lambda: next(times))
    outcomes = [collect.collect(source, *SPAN).failure for _ in range(MAX_ATTEMPTS + 1)]
    assert source.downloads == MAX_ATTEMPTS
    assert outcomes[-1] == "no download: 3 attempts today already, none saved (at most 3)"
    logged = attempts(tmp_path)
    assert tuple(logged[0]) == FIELDS  # times and outcomes only, never a value
    assert [r["outcome"] for r in logged] == [
        "started",
        "download_failed",
        "started",
        "not_publishers_file",
        "started",
        "download_failed",
    ]
    next_day = collector(tmp_path, lambda: datetime(2026, 10, 16, 6, 0, tzinfo=IST))
    assert next_day.collect(source, *SPAN).failure == "" and source.downloads == MAX_ATTEMPTS + 1


def test_a_saved_copy_ends_the_days_downloads(tmp_path):
    source = FlakyCboe([REFUSED, FAKE, FAKE])
    times = iter(datetime(2026, 10, 15, 6, m, tzinfo=IST) for m in range(10))
    collect = collector(tmp_path, lambda: next(times))
    assert collect.collect(source, *SPAN).failure
    assert collect.collect(source, *SPAN).values
    again = collect.collect(source, *SPAN)
    assert source.downloads == 2 and again.skipped.startswith("no download: today's copy")
    assert [r["outcome"] for r in attempts(tmp_path)] == ["started", "download_failed", "started", "saved"]
    assert all(set(r.values()) & {"1000.5", "1001.25"} == set() for r in attempts(tmp_path))


def test_a_cue_without_the_once_a_day_rule_logs_no_attempt(tmp_path):
    source = FakeSource({"a.csv": fake_file(("2026-10-14", 2.0))})
    collector(tmp_path, lambda: PATH_TIME).collect(source, *SPAN)
    assert not (tmp_path / "log" / ATTEMPTS_FOLDER).exists()


def test_an_unexpected_failure_still_counts_and_a_broken_log_lets_no_download_by(tmp_path):
    source = FlakyCboe([RuntimeError("parser crashed")] * 4)
    collect = collector(tmp_path, lambda: PATH_TIME)
    for _ in range(MAX_ATTEMPTS):
        with pytest.raises(RuntimeError):
            collect.collect(source, *SPAN)
    assert collect.collect(source, *SPAN).failure.startswith("no download: 3 attempts")
    assert source.downloads == MAX_ATTEMPTS and {r["outcome"] for r in attempts(tmp_path)} == {"started", "stopped"}
    broken = tmp_path / "broken"
    (broken / "log" / ATTEMPTS_FOLDER).mkdir(parents=True)
    (broken / "log" / ATTEMPTS_FOLDER / "sp500.csv").write_text("attempted_at,outcome\n2026-10-14T06:00:00+05:30,saved")
    fresh = FlakyCboe([FAKE])
    with pytest.raises(TableFileBroken):
        collector(broken, lambda: PATH_TIME).collect(fresh, *SPAN)
    assert fresh.downloads == 0


def test_attempts_count_on_the_ist_date_whatever_the_clocks_zone(tmp_path):
    utc_evening = datetime(2026, 10, 15, 20, 0, tzinfo=UTC)  # 01:30 IST on 16 Oct
    source = FlakyCboe([REFUSED] * 4)
    collect = collector(tmp_path, lambda: utc_evening)
    for _ in range(MAX_ATTEMPTS):
        collect.collect(source, *SPAN)
    assert attempts(tmp_path)[0]["attempted_at"] == "2026-10-16T01:30:00+05:30"
    assert collect.collect(source, *SPAN).failure.startswith("no download")
    assert collector(tmp_path, lambda: PATH_TIME).collect(FlakyCboe([REFUSED]), *SPAN).failure.startswith("download")


def test_a_run_killed_mid_download_still_counts(tmp_path):
    log = tmp_path / "log" / ATTEMPTS_FOLDER / "sp500.csv"
    log.parent.mkdir(parents=True)
    log.write_text("attempted_at,outcome\n" + "2026-10-15T06:00:00+05:30,started\n" * MAX_ATTEMPTS)  # no outcomes
    source = FlakyCboe([FAKE])
    assert collector(tmp_path, lambda: PATH_TIME).collect(source, *SPAN).failure.startswith("no download: 3")
    assert source.downloads == 0
