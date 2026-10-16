"""Story A19 criterion 13: the kick's decision (the cron-behind-a-live-poller sequence planted), the successor rule
and the GitHub adapter."""

from datetime import UTC, datetime, time, timedelta

import pytest

from fno.news.episodes import Episodes
from fno.news.github_runs import GitHubError, GitHubWorkflowRuns
from fno.news.kick import DISPATCH, NOTHING, STOPPED, CompletedRun, decide, wants_successor
from fno.news.kick_cli import cmd_kick
from fno.news.settings import Window
from fno.news.window import PollingWindow
from tests.news.fakes import Alerts, Clock, Committer, MemoryLog, ist

WINDOW = PollingWindow(Window(time(7), time(23)))
DAY, NIGHT = ist(2026, 10, 16, 12, 0), ist(2026, 10, 16, 23, 30)


def completed(conclusion="failure", lasted=timedelta(minutes=30), steps_ran=True):
    return CompletedRun(conclusion, DAY - lasted, DAY, steps_ran, "https://github.com/x/runs/1")


def test_a_cron_behind_a_live_poller_does_nothing():
    """The planted sequence: a poller is running, a cron fires, the poller ends and dispatches its successor."""
    assert decide(DAY, WINDOW, False, active_runs=1).action == NOTHING
    assert decide(DAY, WINDOW, False, active_runs=0, completed=completed("success")).action == NOTHING


def test_a_cron_with_no_poller_starts_one_inside_the_window_only():
    assert decide(DAY, WINDOW, False, 0).action == DISPATCH
    assert decide(NIGHT, WINDOW, False, 0).action == NOTHING
    assert decide(NIGHT, WINDOW, True, 0).action == DISPATCH  # the bridge keeps the chain alive overnight


def test_a_run_replaced_before_any_step_is_ignored():
    assert decide(DAY, WINDOW, False, 0, completed("cancelled", timedelta(seconds=3), False)).action == NOTHING


@pytest.mark.parametrize(
    "lasted, action", [(timedelta(minutes=10), DISPATCH), (timedelta(minutes=9, seconds=59), STOPPED)]
)
def test_failed_runs_restart_only_after_10_minutes(lasted, action):
    assert decide(DAY, WINDOW, False, 0, completed("failure", lasted)).action == action
    assert decide(DAY, WINDOW, False, 0, completed("cancelled", lasted, True)).action == action


def test_a_failed_run_is_not_restarted_while_another_is_queued():
    assert decide(DAY, WINDOW, False, 1, completed()).action == NOTHING


@pytest.mark.parametrize(
    "lasted, now, bridge, wanted",
    [(timedelta(minutes=10), DAY, False, True), (timedelta(minutes=9, seconds=59), DAY, False, False),
     (timedelta(minutes=340), NIGHT, False, False), (timedelta(minutes=340), NIGHT, True, True)],
)  # fmt: skip
def test_successor_rule(lasted, now, bridge, wanted):
    assert wants_successor(lasted, now, WINDOW, bridge) is wanted


class Runs:
    def __init__(self, active=0, done=None, fail=False):
        self.active, self.done, self.fail, self.dispatched = active, done, fail, 0

    def active_count(self):
        if self.fail:
            raise GitHubError("GitHub answered HTTP 502")
        return self.active

    def completed(self, event):
        return self.done

    def dispatch(self):
        self.dispatched += 1


def kick(runs, event, now=DAY):
    log, alerts, printed, committer = MemoryLog(), Alerts(), [], Committer()
    parts = {"runs": runs, "episodes": Episodes(log, alerts, Clock(now), printed.append), "window": WINDOW,
             "bridge": False, "committer": committer, "clock": Clock(now), "event": event}  # fmt: skip
    return cmd_kick(None, printed.append, parts), log, alerts, printed, committer


def test_kick_dispatches_on_a_cron_and_records_nothing():
    runs = Runs()
    code, log, alerts, printed, committer = kick(runs, {"schedule": "43 1 * * *"})
    assert (code, runs.dispatched, log.rows(), committer.calls) == (0, 1, [], 0)


def test_kick_records_a_stopped_restart_once_and_commits_it():
    runs = Runs(done=completed("failure", timedelta(minutes=2)))
    code, log, alerts, printed, committer = kick(runs, {"workflow_run": {"id": 1}})
    assert (code, runs.dispatched, [r.kind for r in log.rows()], committer.calls) == (0, 0, ["restart_stopped"], 1)
    assert len(alerts.sent) == 1


def test_kick_names_a_github_failure_records_it_once_and_exits_1():
    code, log, alerts, printed, committer = kick(Runs(fail=True), {})
    assert code == 1 and any("NOT started" in p for p in printed)
    assert ([r.kind for r in log.rows()], len(alerts.sent), committer.calls) == (["dispatch"], 1, 1)


def test_a_short_failure_at_night_or_beside_a_live_poller_is_nothing():
    short = completed("failure", timedelta(minutes=2))
    assert decide(NIGHT, WINDOW, False, 0, short).action == NOTHING
    assert decide(DAY, WINDOW, False, 1, short).action == NOTHING


class Response:
    def __init__(self, status, body=None):
        self.status_code, self._body = status, body or {}

    def json(self):
        return self._body


class Session:
    def __init__(self, answers):
        self.answers, self.calls = answers, []

    def request(self, method, url, headers=None, timeout=None, **kwargs):
        self.calls.append((method, url, kwargs, headers))
        return self.answers.pop(0)


def test_github_adapter_counts_reads_and_dispatches():
    counts = [Response(200, {"total_count": n}) for n in (1, 0, 0, 0, 0)]
    jobs = Response(200, {"jobs": [{"steps": [{"conclusion": "skipped"}, {"conclusion": "success"}]}]})
    session = Session([*counts, jobs, Response(204)])
    runs = GitHubWorkflowRuns("exepex/trading", "token", session=session)
    assert runs.active_count() == 1
    event = {"workflow_run": {"id": 9, "conclusion": "failure", "run_started_at": "2026-10-16T06:00:00Z",
                              "updated_at": "2026-10-16T06:20:00Z", "html_url": "https://github.com/r/9"}}  # fmt: skip
    run = runs.completed(event)
    assert (run.steps_ran, run.lasted) == (True, timedelta(minutes=20))
    assert run.started_at == datetime(2026, 10, 16, 6, tzinfo=UTC)
    runs.dispatch()
    method, url, kwargs, headers = session.calls[-1]
    assert (method, kwargs["json"]) == ("post", {"ref": "main"}) and url.endswith("news-capture.yml/dispatches")


def test_github_adapter_refusals_are_named():
    with pytest.raises(GitHubError):
        GitHubWorkflowRuns("exepex/trading", "t", session=Session([Response(403)])).active_count()
    with pytest.raises(GitHubError):
        GitHubWorkflowRuns("exepex/trading", "t", session=Session([Response(422)])).dispatch()


def test_no_step_ran_is_read_from_the_jobs():
    jobs = Response(200, {"jobs": [{"steps": []}, {"steps": None}]})
    runs = GitHubWorkflowRuns("exepex/trading", "t", session=Session([jobs]))
    event = {"workflow_run": {"id": 9, "conclusion": "cancelled", "run_started_at": "2026-10-16T06:00:00Z",
                              "updated_at": "2026-10-16T06:00:03Z", "html_url": "u"}}  # fmt: skip
    assert runs.completed(event).steps_ran is False
