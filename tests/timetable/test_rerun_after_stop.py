"""Judge 118 addendum 4, should-fix 1, and decision 47: after a stopped run, the rerun first commits the failed step's
files exactly as recorded, with the real `GitCommitter`, and never repeats a step: one pack build, one decision
collection, one capture, no second fill. A pending file changed since it was recorded stops the rerun with an alert
and is never regenerated."""

import json
import subprocess

import pytest

from fno.books.account import PaperAccount
from fno.constants import BOOK1_RULES, BOOK2_HYBRID
from fno.desk.daily_run import RunStopped
from fno.desk.git_sync import Git, GitCommitter
from fno.desk.pending_commit import PendingCommitter

from .fakes import C4, Decisions, FakePacks, Rules, daily_run
from .test_commit_failure_run import checkout_with_origin, git
from .test_daily_run import NORMAL, decided, run_day
from .test_raw_quote_refusal_run import RAW_QUOTE


class Cause:
    """A raw quote file staged while a step runs: that step's commit is refused; `remove()` is the hand fix."""

    def __init__(self, root):
        self.root = root

    def stage(self):
        (self.root / RAW_QUOTE).parent.mkdir(parents=True, exist_ok=True)
        (self.root / RAW_QUOTE).write_text("contract_id,bid,ask\n", encoding="utf-8")
        git(self.root, "add", "--", RAW_QUOTE)

    def remove(self):
        git(self.root, "rm", "-q", "--cached", "--", RAW_QUOTE)
        (self.root / RAW_QUOTE).unlink()


class FilePacks(FakePacks):
    """Writes the pack file E2 would, counts builds and runs `during` inside the first build."""

    def __init__(self, root, during=None):
        super().__init__()
        self.root, self.during, self.builds = root, during, 0

    def path(self, day):
        return self.root / "journal" / "packs" / day.isoformat() / "common.json"

    def build(self, day):
        pack, self.builds = super().build(day), self.builds + 1
        self.path(day).parent.mkdir(parents=True, exist_ok=True)
        self.path(day).write_text(json.dumps(pack.body, sort_keys=True) + "\n", encoding="utf-8")
        if self.during and self.builds == 1:
            self.during()
        return pack

    def files(self, day):
        return (self.path(day),) if self.path(day).is_file() else ()


class CountedDecisions(Decisions):
    def __init__(self, during=None):
        super().__init__()
        self.during, self.collections = during, 0

    def observe(self):
        self.collections += 1
        if self.during and self.collections == 1:
            self.during()
        return super().observe()


def real_run(root, tmp_path, alerts, decisions, packs):
    checkout_with_origin(root)
    run, clock, capture, _ = daily_run(root, tmp_path, alerts, (BOOK1_RULES, BOOK2_HYBRID), decisions, C4(), Rules())
    committer = PendingCommitter(GitCommitter(Git(root)), root)
    run.committer, run.steps.capture.committer, run.steps.packs = committer, committer, packs
    return run, clock, capture


def committed(root, path):
    return subprocess.run(["git", "-C", str(root), "show", f"HEAD:{path.relative_to(root).as_posix()}"],
                          check=True, capture_output=True).stdout  # fmt: skip


def origin_messages(root):
    return git(root / "origin.git", "log", "--format=%s").splitlines()[::-1][1:]  # oldest first, the start aside


def test_a_stop_at_the_pack_is_committed_as_recorded_on_the_rerun_and_nothing_repeats(root, tmp_path, alerts):
    cause = Cause(root)
    packs, decisions = FilePacks(root, during=cause.stage), Decisions()
    decisions.add(*decided(BOOK1_RULES, "t1", NORMAL), NORMAL)
    run, clock, capture = real_run(root, tmp_path, alerts, decisions, packs)
    with pytest.raises(RunStopped):
        run_day(run, clock, NORMAL)
    assert "run STOPPED at step pack" in alerts.sent[0] and "exits not reviewed today" in alerts.sent[0]
    recorded = packs.path(NORMAL).read_bytes()
    cause.remove()
    log = run.run(NORMAL)  # the hand fix done, the rerun
    assert committed(root, packs.path(NORMAL)) == recorded  # byte-identical, never rebuilt
    assert packs.builds == 1 and len(capture.taken) == 1 and list(log.steps) == [
        "versions", "pack", "decisions", "snapshot", "fills", "exits"]  # fmt: skip
    pack_message = f"Desk run {NORMAL} step pack (committed on the rerun, as recorded)"
    assert origin_messages(root)[:2] == [f"Desk run {NORMAL} step versions", pack_message]
    assert len(PaperAccount(root, BOOK1_RULES).fills()) == 4  # the fly's four legs, filled once
    assert run.run(NORMAL).steps == log.steps and len(PaperAccount(root, BOOK1_RULES).fills()) == 4  # a third run


def test_a_stop_at_the_decisions_never_collects_again(root, tmp_path, alerts):
    """Re-collecting after the deadline would make every book late: the recorded collection is committed instead."""
    cause = Cause(root)
    decisions = CountedDecisions(during=cause.stage)
    decisions.add(*decided(BOOK1_RULES, "t1", NORMAL), NORMAL)  # book 2 decides nothing: its no-decision file
    run, clock, _ = real_run(root, tmp_path, alerts, decisions, FilePacks(root))
    with pytest.raises(RunStopped):
        run_day(run, clock, NORMAL)
    late = next((root / "journal").rglob("no_decision.json"))
    recorded = late.read_bytes()
    cause.remove()
    log = run.run(NORMAL)
    assert decisions.collections == 1 and committed(root, late) == recorded
    assert "run_id" in log.result("decisions")[BOOK1_RULES]  # still on time, as collected
    assert len(PaperAccount(root, BOOK1_RULES).fills()) == 4


def test_a_pending_file_changed_since_it_was_recorded_stops_the_rerun_and_is_never_rebuilt(root, tmp_path, alerts):
    cause = Cause(root)
    packs, decisions = FilePacks(root, during=cause.stage), Decisions()
    run, clock, _ = real_run(root, tmp_path, alerts, decisions, packs)
    with pytest.raises(RunStopped):
        run_day(run, clock, NORMAL)
    cause.remove()
    packs.path(NORMAL).write_text("{}\n", encoding="utf-8")  # tampered after the stop
    head = git(root, "rev-parse", "HEAD")
    with pytest.raises(RunStopped):
        run.run(NORMAL)
    sent = alerts.sent[-1]
    assert "run STOPPED at the rerun's start" in sent and "never regenerated" in sent
    assert f"journal/packs/{NORMAL}/common.json" in sent and "Fix: remove the cause" not in sent
    assert git(root, "rev-parse", "HEAD") == head and packs.builds == 1  # nothing committed, nothing rebuilt


REJECT_EXITS = """#!/bin/sh
while read old new ref; do
  git log -1 --format=%s "$new" | grep -q "step exits" && exit 1
done
exit 0
"""


def test_a_push_rejected_every_time_is_pushed_by_the_rerun(root, tmp_path, alerts):
    """The last step's push is rejected: on the rerun nothing follows the recovery, which must push it itself."""
    run, clock, _ = real_run(root, tmp_path, alerts, Decisions(), FilePacks(root))
    hook = root / "origin.git" / "hooks" / "pre-receive"
    hook.write_text(REJECT_EXITS, encoding="utf-8")
    hook.chmod(0o755)
    with pytest.raises(RunStopped):
        run_day(run, clock, NORMAL)
    assert "run STOPPED at step exits" in alerts.sent[0] and "exits not reviewed today" not in alerts.sent[0]
    assert "the rerun pushes the local commit" in alerts.sent[0]
    hook.unlink()
    run.run(NORMAL)
    assert origin_messages(root)[-1] == f"Desk run {NORMAL} step exits"  # the stuck commit, pushed by the recovery
    assert git(root, "rev-list", "origin/main..HEAD") == ""  # nothing left unpushed
