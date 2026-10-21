"""Story A17e part B, criteria 7 and 5: the newest 5-minute level and its status (20:00 old is live, 20:01 stale, a
level from an earlier day is "market closed"), the private row and raw copy in Drive, and the command's one alert and
one O10 row when an index failed. Every level here is made up; no line or repository file holds one."""

import csv
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from fno.global_cues import preopen_cli
from fno.global_cues.markets import TOKYO
from fno.global_cues.preopen import CLOSED, LIVE, ROW_FIELDS, STALE, PreopenReader, level_status, newest_level
from fno.global_cues.row_log import CsvRowLog
from fno.global_cues.snapshot_log import SnapshotLog
from fno.global_cues.yahoo_source import YahooBlocked, YahooChartSource
from fno.models import IST
from fno.storage.raw_store import LocalFolderStore
from tests.global_cues.world_fakes import CannedResponse, CountingSession, utc, yahoo_chart

TOKYO_ZONE = ZoneInfo("Asia/Tokyo")
SEEN = datetime(2026, 10, 22, 9, 0, tzinfo=IST)  # 12:30 in Tokyo
LEVEL = 12345.67  # made up


@pytest.mark.parametrize(
    ("age", "status"),
    [
        (timedelta(minutes=19, seconds=59), LIVE),
        (timedelta(minutes=20), LIVE),
        (timedelta(minutes=20, seconds=1), STALE),
    ],
)
def test_twenty_minutes_old_is_live_and_twenty_minutes_one_is_stale(age, status):
    assert level_status(SEEN, SEEN - age, TOKYO_ZONE) == status


def test_a_level_from_an_earlier_market_day_is_market_closed():
    yesterday = datetime(2026, 10, 21, 15, 25, tzinfo=TOKYO_ZONE)
    assert level_status(SEEN, yesterday, TOKYO_ZONE) == CLOSED


def answer(*points):
    return yahoo_chart("Asia/Tokyo", list(points))


def test_the_newest_level_is_the_last_point_with_a_value():
    data = answer((utc(date(2026, 10, 22), time(3, 15)), 1.0), (utc(date(2026, 10, 22), time(3, 20)), LEVEL),
                  (utc(date(2026, 10, 22), time(3, 25)), None))  # fmt: skip
    level = newest_level("nikkei225", data, SEEN)
    assert (level.level, level.status) == (LEVEL, LIVE) and level.level_time.hour == 12  # 03:20 UTC = 12:20 Tokyo
    with pytest.raises(ValueError, match="no 5-minute level"):
        newest_level("nikkei225", answer((utc(date(2026, 10, 22), time(3, 20)), None)), SEEN)
    with pytest.raises(ValueError, match="not Yahoo's chart answer"):
        newest_level("nikkei225", b"{}", SEEN)


def reader(tmp_path, session):
    log = CsvRowLog(tmp_path / "private" / "rows.csv")
    archive = LocalFolderStore(tmp_path / "drive")
    found = PreopenReader(session, archive, SnapshotLog(tmp_path / "log"), log,
                          lambda index, seen: ("98.5", "nikkei225"), lambda: SEEN)  # fmt: skip
    return found, log


def source():
    return YahooChartSource("nikkei225_yahoo", "^N225", TOKYO, 7, True)


def test_a_read_archives_the_raw_answer_and_appends_one_private_row(tmp_path):
    data = answer((utc(date(2026, 10, 22), time(3, 20)), LEVEL))
    found, log = reader(tmp_path, CountingSession(CannedResponse(200, data)))
    line = found.read(source(), "nikkei225")
    assert line == "nikkei225: live, level of 12:20 JST (10 min old)" and str(LEVEL) not in line
    (row,) = log.rows()
    assert tuple(row) == ROW_FIELDS and (row["level"], row["status"], row["previous_close_cue"]) == (
        repr(LEVEL),
        LIVE,
        "nikkei225",
    )
    assert [p.name for p in (tmp_path / "drive").rglob("*.json")] == ["090000_nikkei225_5m.json"]
    logged = list(csv.DictReader((tmp_path / "log" / "nikkei225_preopen.csv").open()))
    assert logged[0]["path"].startswith("yahoo/preopen/2026/10/22/") and str(LEVEL) not in str(logged)


def test_a_blocked_read_writes_nothing(tmp_path):
    found, log = reader(tmp_path, CountingSession(CannedResponse(429, b"Too Many Requests")))
    with pytest.raises(YahooBlocked):
        found.read(source(), "nikkei225")
    assert log.rows() == [] and not (tmp_path / "drive").exists()


def test_the_command_alerts_once_and_records_one_o10_row_when_an_index_failed(monkeypatch, tmp_path):
    from fno.health.capture_errors import CaptureErrorLog

    class Reader:
        def read(self, source, index):
            if index == "kospi":
                raise YahooBlocked(
                    "kospi_yahoo: Yahoo answered HTTP 403; stopped for this run, never retried another way"
                )
            return f"{index}: live"

    sent, errors = [], CaptureErrorLog(tmp_path / "capture_errors.csv")
    monkeypatch.setattr(
        "fno.global_cues.wiring.build_preopen", lambda: (Reader(), [("nikkei225", None), ("kospi", None)])
    )
    monkeypatch.setattr(
        "fno.composition.build_alert_sender",
        lambda: type("S", (), {"send": lambda self, t: sent.append(t) or "sent"})(),
    )
    monkeypatch.setattr("fno.health.wiring.build_capture_error_log", lambda: errors)
    out = []
    assert preopen_cli.cmd_preopen(out.append) == 1
    assert out[:2] == ["nikkei225: live", out[1]] and out[1].startswith("kospi: FAILED (YahooBlocked)")
    assert sent == ["Omenix F&O pre-open Asian levels: kospi failed (the routine's output names why)"]
    (row,) = errors.rows()
    assert (row.job, row.step, row.kind, row.message) == ("global-cues-preopen", "preopen", "failure", "failed: kospi")


def test_the_command_exits_0_and_records_nothing_when_every_index_read(monkeypatch):
    class Reader:
        def read(self, source, index):
            return f"{index}: {CLOSED}"  # an Asian holiday is a good run

    monkeypatch.setattr("fno.global_cues.wiring.build_preopen", lambda: (Reader(), [("nikkei225", None)]))
    monkeypatch.setattr("fno.health.wiring.build_capture_error_log", lambda: pytest.fail("no row when nothing failed"))
    assert preopen_cli.cmd_preopen(lambda line: None) == 0
