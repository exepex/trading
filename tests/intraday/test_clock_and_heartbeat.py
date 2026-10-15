"""Story A16 criteria 8 (host clock vs GitHub's and Slack's server times) and 9 (heartbeat and the silence check)."""

import subprocess
from datetime import date, datetime
from pathlib import Path

import pytest
import requests

from fno.intraday.cli import heartbeat_check
from fno.intraday.clock import CLOCK_OK, CLOCK_SKEW, CLOCK_UNCHECKED, ClockCheck, HttpDateClock
from fno.intraday.document import utc_text
from fno.intraday.heartbeat import NOT_WATCHED, OK, SILENT, Heartbeat, PublishedHeartbeat, heartbeat_state
from fno.models import IST
from tests.intraday.fakes import DAY, FakeAlerts, FixedServer, calendar, ist


class DateSession:
    def __init__(self, date_header: str | None = None, error: Exception | None = None):
        self.date_header, self.error = date_header, error

    def head(self, url, timeout):
        if self.error:
            raise self.error
        response = requests.Response()
        if self.date_header:
            response.headers["Date"] = self.date_header
        return response


def test_the_skew_is_host_minus_server_allowing_for_the_dropped_fraction():
    host = ist(DAY, 9, 30, 10)  # 04:00:10 UTC
    clock = HttpDateClock("github", "https://x", lambda: host, DateSession("Thu, 15 Oct 2026 04:00:03 GMT"))
    assert clock.skew_seconds() == pytest.approx(6.5)


@pytest.mark.parametrize("session", [DateSession(None), DateSession(error=requests.ConnectionError())])
def test_no_time_from_a_server_is_none(session):
    assert HttpDateClock("slack", "https://x", lambda: ist(DAY, 9, 30), session).skew_seconds() is None


@pytest.mark.parametrize(
    "skews, status",
    [((5.0, 0.2), CLOCK_OK), ((-5.0, None), CLOCK_OK), ((5.01, 0.2), CLOCK_SKEW), ((0.1, -5.01), CLOCK_SKEW),
     ((None, None), CLOCK_UNCHECKED)],
)  # fmt: skip
def test_the_5_second_limit_and_the_unchecked_case(skews, status):
    reading = ClockCheck([FixedServer("github", skews[0]), FixedServer("slack", skews[1])]).check()
    assert reading.status == status
    assert reading.warning().startswith("WARNING: host clock differs") == (status == CLOCK_SKEW)


def beat(finished: datetime) -> dict:
    return {"run_finished_at": utc_text(finished)}


@pytest.mark.parametrize(
    "now, finished, recorded, status",
    [
        (ist(DAY, 10, 30), ist(DAY, 10, 0), True, OK),  # exactly 30 minutes: not yet silent
        (ist(DAY, 10, 30, 1), ist(DAY, 10, 0), True, SILENT),
        (ist(DAY, 9, 44, 59), ist(date(2026, 10, 14), 15, 31), True, NOT_WATCHED),  # before 09:45
        (ist(DAY, 9, 45), ist(date(2026, 10, 14), 15, 31), True, SILENT),  # yesterday's beat at 09:45
        (ist(DAY, 15, 45), ist(DAY, 15, 14), True, SILENT),
        (ist(DAY, 15, 45, 1), ist(DAY, 15, 14), True, NOT_WATCHED),
        (ist(DAY, 12, 0), ist(DAY, 9, 0), False, NOT_WATCHED),  # not a recorded session
    ],
)
def test_the_silence_rule_at_its_limits(now, finished, recorded, status):
    assert heartbeat_state(beat(finished), now, recorded).status == status


def test_no_heartbeat_at_all_is_silent_in_watched_hours():
    assert heartbeat_state(None, ist(DAY, 11, 0), True).status == SILENT


def test_the_check_alerts_a_warning_with_what_to_do_and_exits_1(tmp_path, capsys):
    heartbeat, alerts = Heartbeat(tmp_path), FakeAlerts()
    heartbeat.write(beat(ist(DAY, 10, 0)))
    assert heartbeat_check(heartbeat, calendar(), alerts, ist(DAY, 11, 0)) == 1
    assert alerts.sent[0].startswith("Action: check the 15-minute recorder's routine") and "WARNING" in alerts.sent[0]
    assert "alert sent to #fno-desk" in capsys.readouterr().out


def test_the_check_is_quiet_when_fresh_or_on_a_holiday(tmp_path):
    heartbeat, alerts = Heartbeat(tmp_path), FakeAlerts()
    heartbeat.write(beat(ist(DAY, 10, 50)))
    assert heartbeat_check(heartbeat, calendar(), alerts, ist(DAY, 11, 0)) == 0
    assert heartbeat_check(heartbeat, calendar(), alerts, ist(date(2026, 10, 20), 11, 0)) == 0
    assert not alerts.sent


def test_the_check_stops_loudly_outside_the_calendar(tmp_path, capsys):
    alerts = FakeAlerts()
    assert heartbeat_check(Heartbeat(tmp_path), calendar(), alerts, ist(date(2027, 1, 4), 11, 0)) == 1
    assert alerts.sent and "15-minute recorder stopped" in capsys.readouterr().out


def test_times_compare_across_offsets():
    assert heartbeat_state(beat(ist(DAY, 10, 0)), ist(DAY, 10, 10).astimezone(IST), True).status == OK


class Git:
    def __init__(self, fetch=0, show=0, text='{"run_finished_at": "2026-10-15T04:30:00+00:00"}'):
        self.codes, self.text, self.calls = {"fetch": fetch, "show": show}, text, []

    def __call__(self, args, cwd, capture_output, text):
        self.calls.append(args[1])
        return subprocess.CompletedProcess(args, self.codes[args[1]], self.text, "")


def test_githubs_copy_is_fetched_and_read():
    git = Git()
    beat = PublishedHeartbeat(Path("."), "research/data/intraday/heartbeat.json", run=git).read()
    assert beat == {"run_finished_at": "2026-10-15T04:30:00+00:00"} and git.calls == ["fetch", "show"]


@pytest.mark.parametrize("git", [Git(fetch=1), Git(show=128), Git(text="{not json"), Git(text="[1, 2]")])
def test_an_unreachable_or_unreadable_copy_is_none_and_reads_as_silent(git):
    beat = PublishedHeartbeat(Path("."), "x.json", run=git).read()
    assert beat is None and heartbeat_state(beat, ist(DAY, 11, 0), True).status == SILENT


def test_a_corrupt_local_heartbeat_or_time_reads_as_silent(tmp_path):
    (tmp_path / "heartbeat.json").write_text("{broken")
    assert Heartbeat(tmp_path).read() is None
    assert heartbeat_state({"run_finished_at": "garbage"}, ist(DAY, 11, 0), True).status == SILENT
