"""Judge 118 addendum 3, should-fix 1, and decision 44: with the real `GitCommitter` in a daily run, a failed commit
(a staged raw quote file, or a pull that cannot reach origin) stops the run at that step with one alert naming why,
commits nothing and raises `RunStopped`; never an unhandled refusal."""

import shutil
import subprocess

import pytest

from fno.books.account import PaperAccount
from fno.constants import BOOK1_RULES
from fno.desk.daily_ports import CommitFailed
from fno.desk.daily_run import RunStopped
from fno.desk.git_sync import Git, GitCommitter
from fno.desk.pending_commit import PendingCommitter

from .fakes import C4, RAW_QUOTE, Commits, Decisions, Rules, daily_run
from .test_daily_run import NORMAL, decided, run_day


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout


def checkout_with_origin(root):
    """`root` (the started accounts) as a committed checkout pushing to a bare origin beside it."""
    origin = root / "origin.git"
    git(root, "init", "-q", "-b", "main")
    for key, value in (("user.email", "t@example.org"), ("user.name", "t"), ("core.hooksPath", "/dev/null")):
        git(root, "config", key, value)
    (root / ".git" / "info" / "exclude").write_text("origin.git/\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "started accounts")
    subprocess.run(["git", "clone", "-q", "--bare", str(root), str(origin)], check=True, capture_output=True)
    git(root, "remote", "add", "origin", str(origin))
    git(root, "fetch", "-q", "origin")
    return origin


def stopped_run(root, tmp_path, alerts, commits_locally=False):
    decisions = Decisions()
    decisions.add(*decided(BOOK1_RULES, "t1", NORMAL), NORMAL)
    run, clock, *_ = daily_run(root, tmp_path, alerts, (BOOK1_RULES,), decisions, C4(), Rules())
    run.committer = PendingCommitter(GitCommitter(Git(root)), root)
    head = git(root, "rev-parse", "HEAD")
    with pytest.raises(RunStopped) as stopped:
        run_day(run, clock, NORMAL)
    assert (git(root, "rev-parse", "HEAD") != head) == commits_locally  # otherwise nothing committed
    assert len(alerts.sent) == 1 and alerts.sent[0] == str(stopped.value)
    return alerts.sent[0]


def test_a_staged_raw_quote_file_stops_the_run_with_one_alert_naming_it(root, tmp_path, alerts):
    origin = checkout_with_origin(root)
    (root / RAW_QUOTE).parent.mkdir(parents=True)
    (root / RAW_QUOTE).write_text("contract_id,bid,ask\n", encoding="utf-8")
    git(root, "add", "--", RAW_QUOTE)
    sent = stopped_run(root, tmp_path, alerts)
    assert "run STOPPED at step versions" in sent and "nifty_20261014_151500.csv" in sent
    assert git(origin, "log", "--oneline").count("\n") == 1  # nothing pushed
    assert git(root, "diff", "--cached", "--name-only").split() == [RAW_QUOTE]  # the run's own add was undone


def test_a_pull_that_cannot_reach_origin_stops_the_run_with_one_alert(root, tmp_path, alerts):
    shutil.rmtree(checkout_with_origin(root))
    sent = stopped_run(root, tmp_path, alerts)
    assert "run STOPPED at step versions" in sent and "git fetch -q failed" in sent  # the stray check fetches first


def test_a_push_rejected_every_time_stops_the_run_with_one_alert(root, tmp_path, alerts):
    """Judge 118 addendum 3's older case, at the same catch point: the commit stays local and unpushed, which also
    refuses every later account write until it is resolved by hand (fail closed)."""
    origin = checkout_with_origin(root)
    hook = origin / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    sent = stopped_run(root, tmp_path, alerts, commits_locally=True)
    assert "run STOPPED at step versions" in sent and "rejected 3 times; the commit stays local, unpushed" in sent
    assert git(origin, "log", "--oneline").count("\n") == 1  # nothing pushed


class FailingOn(Commits):
    """Fails the commit whose message holds `what`, as `GitCommitter` reports any failure."""

    def __init__(self, clock, what):
        super().__init__(clock)
        self.what = what

    def commit(self, paths, message, own_unpushed=None):
        if self.what in message:
            raise CommitFailed(f"push of '{message}' rejected 3 times")
        return super().commit(paths, message, own_unpushed)


def test_a_failed_commit_inside_a_step_stops_the_run_at_that_step(root, tmp_path, alerts):
    decisions = Decisions()
    decisions.add(*decided(BOOK1_RULES, "t1", NORMAL), NORMAL)
    run, clock, *_ = daily_run(root, tmp_path, alerts, (BOOK1_RULES,), decisions, C4(), Rules())
    run.steps.capture.committer = PendingCommitter(FailingOn(clock, "Execution capture"), root)
    with pytest.raises(RunStopped):
        run_day(run, clock, NORMAL)
    (sent,) = alerts.sent
    assert "run STOPPED at step snapshot" in sent and "Execution capture" in sent
    assert PaperAccount(root, BOOK1_RULES).fills() == []  # no fill and no exit step after it
