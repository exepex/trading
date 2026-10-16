"""The remote observer (story F1t criterion 3e): it reads the remote at each deadline whatever else runs, records a
failed reading as failed, and only asks the remote (the checkout is untouched)."""

import subprocess
from argparse import Namespace
from datetime import datetime, timedelta

from fno.ai.cli import cmd_ai
from fno.ai.observed_receipts import ObservationFile
from fno.ai.remote_observer import GitLsRemote, RemoteHead, RemoteHeadFailed, RemoteObserver
from fno.models import IST

FIRST = datetime(2026, 10, 19, 15, 10, tzinfo=IST)
SECOND = datetime(2026, 10, 19, 15, 11, tzinfo=IST)


class Clock:
    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += timedelta(seconds=seconds)


class Heads(RemoteHead):
    def __init__(self, *answers):
        self.answers = list(answers)

    def head(self):
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def test_it_waits_for_each_deadline_and_records_the_head_then(tmp_path):
    clock, out = Clock(FIRST - timedelta(minutes=5)), ObservationFile(tmp_path / "obs.json")
    RemoteObserver(Heads("c1", "c2"), out, clock, clock.sleep).run([SECOND, FIRST])
    readings = out.read()
    assert [(o.deadline, o.started_at, o.commit) for o in readings] == [(FIRST, FIRST, "c1"), (SECOND, SECOND, "c2")]
    assert all(not o.problem() for o in readings)


def test_a_failed_reading_is_written_as_failed_and_the_next_still_taken(tmp_path):
    clock, out = Clock(FIRST), ObservationFile(tmp_path / "obs.json")
    RemoteObserver(Heads(RemoteHeadFailed("no network"), "c2"), out, clock, clock.sleep).run([FIRST, SECOND])
    first, second = out.read()
    assert (first.commit, first.error) == (None, "no network") and "failed" in first.problem()
    assert second.commit == "c2"


def test_started_after_a_deadline_it_reads_at_once_and_the_reading_shows_how_late(tmp_path):
    clock, out = Clock(FIRST + timedelta(seconds=45)), ObservationFile(tmp_path / "obs.json")
    RemoteObserver(Heads("c1"), out, clock, clock.sleep).run([FIRST])
    assert "started 45 s after" in out.read()[0].problem()


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def test_git_ls_remote_reads_the_remote_head_without_touching_the_checkout(tmp_path):
    remote, work = tmp_path / "remote.git", tmp_path / "work"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    _git(tmp_path, "clone", "-q", str(remote), str(work))
    _git(work, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "one")
    _git(work, "push", "-q", "origin", "HEAD:main")
    pushed = _git(work, "rev-parse", "HEAD")
    _git(work, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "local only")
    local = _git(work, "rev-parse", "HEAD")
    assert GitLsRemote(work).head() == pushed
    assert _git(work, "rev-parse", "HEAD") == local and _git(work, "status", "--porcelain") == ""


def test_git_ls_remote_failure_is_a_failed_reading(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    _git(work, "init", "-q")
    try:
        GitLsRemote(work).head()
    except RemoteHeadFailed as failed:
        assert "git ls-remote failed" in str(failed)
    else:
        raise AssertionError("no remote must be a failed reading")


def test_the_command_refuses_a_deadline_without_a_time_zone(tmp_path, capsys):
    args = Namespace(ai_cmd="observe-remote", out=tmp_path / "o.json", deadline=[datetime(2026, 10, 19, 15, 10)])
    assert cmd_ai(args) == 1
    assert "time zone" in capsys.readouterr().out
