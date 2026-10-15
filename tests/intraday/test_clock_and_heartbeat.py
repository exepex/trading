"""Story A16 criteria 8 (host clock vs GitHub's and Slack's server times) and 9 (heartbeat and the silence check)."""

import subprocess
from datetime import date, datetime
from pathlib import Path

import pytest

from fno.intraday.cli import heartbeat_check
from fno.intraday.clock import CLOCK_OK, CLOCK_PARTIAL, CLOCK_SKEW, CLOCK_UNCHECKED, ClockCheck
from fno.intraday.document import utc_text
from fno.intraday.heartbeat import NOT_WATCHED, OK, SILENT, Heartbeat, PublishedHeartbeat, heartbeat_state
from fno.models import IST
from fno.server_clock import GITHUB_TIME_URL, HttpDateClock
from tests.intraday.fakes import DAY, FakeAlerts, FixedServer, calendar, ist


class Answer:
    def __init__(self, status: int, date_header: str | None):
        self.status_code, self.headers = status, ({"Date": date_header} if date_header else {})


HOST = ist(DAY, 9, 30, 10)  # 04:00:10 UTC


def http_clock(status: int, date_header: str | None, seen: list | None = None) -> HttpDateClock:
    def head(url, timeout):
        (seen if seen is not None else []).append(url)
        return Answer(status, date_header)

    return HttpDateClock("github", GITHUB_TIME_URL.format(repository="exepex/trading"), head)


def test_a_2xx_answer_with_a_date_is_read_and_the_skew_counts_the_one_second_resolution():
    reading = ClockCheck([http_clock(200, "Thu, 15 Oct 2026 04:00:03 GMT")], lambda: HOST).check()
    assert reading.status == CLOCK_SKEW and reading.worst == pytest.approx(6.0)  # 7 s outside, less 1 s resolution


@pytest.mark.parametrize("status", [400, 404, 500])
def test_an_error_answer_carrying_a_date_is_ignored(status):
    """Judge 108 addendum 3 should-fix 2 (judge 101's T1 finding): a proxy's error answer has the proxy's time."""
    reading = ClockCheck([http_clock(status, "Thu, 15 Oct 2026 04:00:10 GMT")], lambda: HOST).check()
    assert reading.status == CLOCK_UNCHECKED and "not trusted" in reading.warning()


def test_github_is_asked_at_the_repository_path_never_the_api_root():
    seen = []
    ClockCheck([http_clock(200, "Thu, 15 Oct 2026 04:00:10 GMT", seen)], lambda: HOST).check()
    assert seen == ["https://api.github.com/repos/exepex/trading"]


@pytest.mark.parametrize(
    "offsets, status",
    [((5.0, 0.2), CLOCK_OK), ((-5.0, 0.0), CLOCK_OK), ((5.01, 0.2), CLOCK_SKEW), ((0.1, -5.01), CLOCK_SKEW),
     ((0.2, None), CLOCK_PARTIAL), ((None, None), CLOCK_UNCHECKED)],
)  # fmt: skip
def test_the_5_second_limit_a_partial_check_and_the_unchecked_case(offsets, status):
    servers = [FixedServer("github", offsets[0], lambda: HOST), FixedServer("slack", offsets[1], lambda: HOST)]
    reading = ClockCheck(servers, lambda: HOST).check()
    assert reading.status == status
    assert bool(reading.warning()) == (status != CLOCK_OK)  # a skew or an unchecked server is always said


def test_the_wiring_asks_github_at_the_repository_and_slack(tmp_path, monkeypatch):
    from fno.intraday import wiring
    from tests.intraday.groww_fakes import FakeGrowwProvider

    monkeypatch.setattr(wiring, "GrowwProvider", lambda cfg: FakeGrowwProvider())
    servers = wiring.build_intraday_recorder({}, tmp_path / "dry").clock_check.servers
    assert [(s.name, s.url) for s in servers] == [
        ("github", "https://api.github.com/repos/exepex/trading"), ("slack", "https://slack.com/api/api.test")
    ]  # fmt: skip


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
