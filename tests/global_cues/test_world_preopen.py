"""Story A17e part B, criteria 7 and 5: the newest 5-minute level and its status (20:00 old is live, 20:01 stale, a
level from an earlier day is "market closed"), the private row and raw copy in Drive, and the command's one alert and
one O10 row when an index failed. Every level here is made up; no line or repository file holds one."""

import csv
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from fno.global_cues import preopen_cli
from fno.global_cues import wiring as global_cues_wiring
from fno.global_cues.markets import SEOUL, TOKYO
from fno.global_cues.preopen import CLOSED, LIVE, LUNCH, ROW_FIELDS, STALE, PreopenReader, level_status, newest_level
from fno.global_cues.row_log import CsvRowLog
from fno.global_cues.snapshot_log import SnapshotLog
from fno.global_cues.yahoo_source import YahooBlocked, YahooChartSource
from fno.models import IST
from fno.storage.raw_store import LocalFolderStore
from tests.global_cues.world_fakes import CannedResponse, CountingSession, utc, yahoo_chart

TOKYO_ZONE = ZoneInfo("Asia/Tokyo")
REAL_COMMITTERS = global_cues_wiring.build_preopen_committers  # before the fixture below fakes it


def at_0855():
    return datetime(2026, 10, 22, 8, 55, tzinfo=IST)


def always(day):
    return True


def no_sleep(seconds):
    raise AssertionError("no wait inside the window")


@pytest.fixture(autouse=True)
def no_commits(monkeypatch):
    """The command's own commit, faked: the git committers are A16e's, tested there."""
    monkeypatch.setattr("fno.global_cues.wiring.build_preopen_committers", lambda: [Committed()])


class Committed:
    def __init__(self, line="pre-open logs committed and pushed (1 file(s))"):
        self.line, self.whats = line, []

    def commit(self, what):
        self.whats.append(what)
        return self.line


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
    assert level_status(SEEN, SEEN - age, SEOUL) == status


def test_a_level_from_an_earlier_market_day_is_market_closed():
    yesterday = datetime(2026, 10, 21, 15, 25, tzinfo=TOKYO_ZONE)
    assert level_status(SEEN, yesterday, TOKYO) == CLOSED


def test_tokyos_lunch_break_reads_lunch_break_not_stale():
    """Tokyo breaks 11:30-12:30 JST (08:00-09:00 IST): at 08:50 IST its 11:30 level is the morning's last, not late."""
    at_lunch, after = datetime(2026, 10, 22, 8, 50, tzinfo=IST), datetime(2026, 10, 22, 9, 0, tzinfo=IST)
    morning_last = datetime(2026, 10, 22, 11, 30, tzinfo=TOKYO_ZONE)
    assert level_status(at_lunch, morning_last, TOKYO) == LUNCH
    assert level_status(after, morning_last, TOKYO) == STALE  # 12:30 JST: the break is over, no new level yet
    assert level_status(at_lunch, morning_last, SEOUL) == STALE  # Seoul has no lunch break


def answer(*points):
    return yahoo_chart("Asia/Tokyo", list(points))


def test_the_newest_level_is_the_last_point_with_a_value():
    data = answer((utc(date(2026, 10, 22), time(3, 15)), 1.0), (utc(date(2026, 10, 22), time(3, 20)), LEVEL),
                  (utc(date(2026, 10, 22), time(3, 25)), None))  # fmt: skip
    level = newest_level("nikkei225", data, SEEN, TOKYO)
    assert (level.level, level.status) == (LEVEL, LIVE)
    assert f"{level.level_time:%H:%M}" == "12:25"  # the 03:20 UTC bar (12:20 Tokyo) ends at 12:25
    with pytest.raises(ValueError, match="no 5-minute level"):
        newest_level("nikkei225", answer((utc(date(2026, 10, 22), time(3, 20)), None)), SEEN, TOKYO)
    with pytest.raises(ValueError, match="not Yahoo's chart answer"):
        newest_level("nikkei225", b"{}", SEEN, TOKYO)


def test_a_level_is_never_shown_and_unequal_times_and_closes_are_refused():
    bad = answer((utc(date(2026, 10, 22), time(3, 20)), "38123.5x"))
    with pytest.raises(ValueError) as refused:
        newest_level("nikkei225", bad, SEEN, TOKYO)
    assert "38123" not in str(refused.value)
    uneven = answer((utc(date(2026, 10, 22), time(3, 15)), 1.0)).replace(b'"close": [1.0]', b'"close": [1.0, 2.0]')
    with pytest.raises(ValueError, match="not one close per timestamp"):
        newest_level("nikkei225", uneven, SEEN, TOKYO)


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
    line, status = found.read(source(), "nikkei225")
    assert line == "nikkei225: live, level of 12:25 JST (5 min old)" and str(LEVEL) not in line and status == LIVE
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
            return f"{index}: live", LIVE

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
    assert preopen_cli.cmd_preopen(out.append, now=at_0855, sleep=no_sleep, is_session=always) == 1
    assert out[:2] == ["nikkei225: live", out[1]] and out[1].startswith("kospi: FAILED (YahooBlocked)")
    assert sent == ["Omenix F&O pre-open Asian levels: kospi failed (the routine's output names why)"]
    (row,) = errors.rows()
    assert (row.job, row.step, row.kind, row.message) == ("global-cues-preopen", "preopen", "failure", "kospi failed")


def test_the_command_exits_0_and_records_nothing_when_every_index_read(monkeypatch):
    class Reader:
        def read(self, source, index):
            return f"{index}: {CLOSED}", CLOSED  # an Asian holiday is a good run

    monkeypatch.setattr("fno.global_cues.wiring.build_preopen", lambda: (Reader(), [("nikkei225", None)]))
    monkeypatch.setattr("fno.health.wiring.build_capture_error_log", lambda: pytest.fail("no row when nothing failed"))
    assert preopen_cli.cmd_preopen(lambda line: None, now=at_0855, sleep=no_sleep, is_session=always) == 0


def _alerts(monkeypatch, tmp_path):
    from fno.health.capture_errors import CaptureErrorLog

    sent, errors = [], CaptureErrorLog(tmp_path / "capture_errors.csv")
    sender = type("S", (), {"send": lambda self, text: sent.append(text) or "sent"})()
    monkeypatch.setattr("fno.composition.build_alert_sender", lambda: sender)
    monkeypatch.setattr("fno.health.wiring.build_capture_error_log", lambda: errors)
    return sent, errors


def test_a_drive_failure_while_building_alerts_and_records_too(monkeypatch, tmp_path):
    from fno.storage.owner_token import DriveSignInRefused

    sent, errors = _alerts(monkeypatch, tmp_path)

    def refused():
        raise DriveSignInRefused("the refresh token was revoked")

    monkeypatch.setattr("fno.global_cues.wiring.build_preopen", refused)
    out = []
    assert preopen_cli.cmd_preopen(out.append, now=at_0855, sleep=no_sleep, is_session=always) == 1
    assert out[0] == "preopen: STOPPED before any read (DriveSignInRefused)"
    assert sent == [preopen_cli.ALERT.format(what="stopped before any read (DriveSignInRefused)")]
    assert [r.message for r in errors.rows()] == ["stopped before any read (DriveSignInRefused)"]


def test_a_failed_archive_write_alerts_and_the_next_indexes_still_read(monkeypatch, tmp_path):
    sent, errors = _alerts(monkeypatch, tmp_path)

    class Reader:
        def read(self, source, index):
            if index == "nikkei225":
                raise RuntimeError("Drive refused the write")
            return f"{index}: live", LIVE

    monkeypatch.setattr(
        "fno.global_cues.wiring.build_preopen", lambda: (Reader(), [("nikkei225", None), ("kospi", None)])
    )
    out = []
    assert (
        preopen_cli.cmd_preopen(out.append, now=at_0855, sleep=no_sleep, is_session=always) == 1
        and "kospi: live" in out
    )
    assert len(sent) == 1 and len(errors.rows()) == 1


def test_every_open_market_stale_alerts_but_stale_beside_a_live_one_does_not(monkeypatch, tmp_path):
    sent, errors = _alerts(monkeypatch, tmp_path)
    statuses = {"nikkei225": STALE, "kospi": STALE, "hang_seng": CLOSED}

    class Reader:
        def read(self, source, index):
            return f"{index}: {statuses[index]}", statuses[index]

    pairs = [(index, None) for index in statuses]
    monkeypatch.setattr("fno.global_cues.wiring.build_preopen", lambda: (Reader(), pairs))
    assert preopen_cli.cmd_preopen(lambda line: None, now=at_0855, sleep=no_sleep, is_session=always) == 1
    assert sent == [
        "Omenix F&O pre-open Asian levels: no live level: every open market stale (the routine's output names why)"
    ]
    statuses["kospi"] = LIVE
    assert (
        preopen_cli.cmd_preopen(lambda line: None, now=at_0855, sleep=no_sleep, is_session=always) == 0
        and len(sent) == 1
    )


def test_it_waits_for_0850_reads_until_0905_and_then_reports_the_rest_unread(monkeypatch, tmp_path):
    sent, errors = _alerts(monkeypatch, tmp_path)
    times = [(8, 40), (8, 40), (8, 50), (9, 4), (9, 5)]  # the day, the wait, then one reading per index
    clock = iter(datetime(2026, 10, 22, h, m, tzinfo=IST) for h, m in times)
    slept = []

    class Reader:
        def read(self, source, index):
            return f"{index}: live", LIVE

    pairs = [("nikkei225", None), ("kospi", None), ("asx200", None)]
    monkeypatch.setattr("fno.global_cues.wiring.build_preopen", lambda: (Reader(), pairs))
    out = []
    assert preopen_cli.cmd_preopen(out.append, now=lambda: next(clock), sleep=slept.append, is_session=always) == 1
    assert slept == [600.0]  # 08:40 to 08:50
    assert out[:3] == ["nikkei225: live", "kospi: live", "asx200: FAILED, not read: the window closed at 09:05 IST"]
    assert sent == [preopen_cli.ALERT.format(what="asx200 failed")]


def test_receipts_that_could_not_be_pushed_alert_and_record(monkeypatch, tmp_path):
    sent, errors = _alerts(monkeypatch, tmp_path)

    class Reader:
        def read(self, source, index):
            return f"{index}: live", LIVE

    refused = Committed("pre-open logs NOT committed: push failed: rejected. Commit research/... by hand")
    monkeypatch.setattr("fno.global_cues.wiring.build_preopen", lambda: (Reader(), [("nikkei225", None)]))
    monkeypatch.setattr("fno.global_cues.wiring.build_preopen_committers", lambda: [refused])
    out = []
    assert preopen_cli.cmd_preopen(out.append, now=at_0855, sleep=no_sleep, is_session=always) == 1
    assert refused.whats == ["pre-open Asian levels"] and refused.line in out
    assert sent == [preopen_cli.ALERT.format(what="receipts not committed")] and errors.rows() == []


def test_the_committers_own_only_part_bs_files():
    from fno.global_cues import wiring

    logs, errors = REAL_COMMITTERS()
    assert logs.owned == tuple(f"research/data/manifests/global-cues/{i}_preopen.csv" for i in wiring.PREOPEN_INDEXES)
    assert errors.owned == ("research/ops/capture_errors.csv",)


def test_a_read_failure_and_a_failed_push_give_one_alert_and_the_row_is_written_before_the_commit(
    monkeypatch, tmp_path
):
    sent, errors = _alerts(monkeypatch, tmp_path)
    rows_at_commit = []

    class Reader:
        def read(self, source, index):
            raise YahooBlocked("kospi_yahoo: Yahoo answered HTTP 403; stopped for this run, never retried another way")

    class Refused(Committed):
        def commit(self, what):
            rows_at_commit.append(len(errors.rows()))
            return "O10 row NOT committed: push failed: rejected"

    monkeypatch.setattr("fno.global_cues.wiring.build_preopen", lambda: (Reader(), [("kospi", None)]))
    monkeypatch.setattr("fno.global_cues.wiring.build_preopen_committers", lambda: [Refused()])
    assert preopen_cli.cmd_preopen(lambda line: None, now=at_0855, sleep=no_sleep, is_session=always) == 1
    assert rows_at_commit == [1]  # the O10 row existed when the commit ran
    assert sent == [preopen_cli.ALERT.format(what="kospi failed; receipts not committed")]


def test_a_day_nse_does_not_trade_reads_nothing(monkeypatch):
    monkeypatch.setattr("fno.global_cues.wiring.build_preopen", lambda: pytest.fail("nothing is read on a closed day"))
    out = []
    assert preopen_cli.cmd_preopen(out.append, now=at_0855, sleep=no_sleep, is_session=lambda day: False) == 0
    assert out == [preopen_cli.NOT_A_TRADING_DAY]


def test_a_day_the_calendar_cannot_answer_alerts_and_records_once(monkeypatch, tmp_path):
    from fno.research_data.calendar import CalendarError

    sent, errors = _alerts(monkeypatch, tmp_path)

    def unknown(day):
        raise CalendarError("2027 is not in the calendar yet")

    monkeypatch.setattr("fno.global_cues.wiring.build_preopen", lambda: pytest.fail("nothing is read"))
    out = []
    assert preopen_cli.cmd_preopen(out.append, now=at_0855, sleep=no_sleep, is_session=unknown) == 1
    assert sent == [preopen_cli.ALERT.format(what="NSE calendar cannot answer for today")]
    assert [r.message for r in errors.rows()] == ["NSE calendar cannot answer for today"]
