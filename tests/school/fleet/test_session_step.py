"""Story MS-P1j with MS-INS part e: the step after the session's outcomes (the instructor's run) sees the sealed
outcomes before the counts are written, can never stop the school's record, and runs again on a rerun. One committer
per run (judge 523): the work only computes; its writes run on the run's own thread and only when the work ended in
time, so a work that finishes after its limit has nothing committed, on real git."""

import subprocess
import threading
import time

from fno.school.constants import SLOT_1500, RecordKind
from fno.school.contracts.fleet import RunMode
from fno.school.dashcam.names import counts_path
from fno.school.fakes import FakeDriver, FakeMaxLossLaw
from fno.school.fleet.counts_commit import SessionFilesCommitter
from fno.school.fleet.counts_file import SessionCounts
from fno.school.fleet.session_hook import StagedSessionStep
from tests.school.contracts import builders as b
from tests.school.fleet.rig import Rig, all_roads
from tests.school.fleet.test_counts_commit import clone, git  # noqa: F401 - the real-git fixture

LAWS = (FakeMaxLossLaw(10_000),)
INSTRUCTOR_FILE = "research/school/counts/instructor/2026/10/20261022.csv"


def rig_with(tmp_path, step) -> Rig:
    rig = Rig(tmp_path, (FakeDriver(all_roads("CS1"), b.put_spread()),), LAWS)
    rig.fleet.after_outcomes = step
    return rig


def writing(root, delay: float = 0.0, seen: list | None = None):
    """A work that takes `delay` seconds, then returns writes that put the instructor's counts file under `root`."""

    def writes():
        (seen if seen is not None else []).append(threading.get_ident())
        (root / INSTRUCTOR_FILE).parent.mkdir(parents=True, exist_ok=True)
        (root / INSTRUCTOR_FILE).write_text("session,driver\n")

    def work(session):
        time.sleep(delay)
        return writes

    return work


def test_the_step_runs_once_the_outcomes_are_sealed_and_before_the_counts_are_written(tmp_path):
    seen = []

    def step(session):
        seen.append((rig.dashcam.find(session, SLOT_1500, RecordKind.OUTCOMES) is not None,
                     (tmp_path / counts_path(session, SLOT_1500)).is_file()))  # fmt: skip

    rig = rig_with(tmp_path, step)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert seen == [(True, False)]


def test_a_failing_or_slow_step_alerts_once_by_class_and_the_counts_are_still_written(tmp_path):
    def broken(session):
        raise KeyError("ContractKey(strike=51200)")

    for name, work in (("broken", broken), ("slow", writing(tmp_path / "slow", delay=0.3))):
        alerts = []
        root = tmp_path / name
        rig = rig_with(root, StagedSessionStep("instructor", work, alerts.append, seconds=0.1))
        rig.fleet.run(b.SESSION, RunMode.REPLAY)
        assert (root / counts_path(b.SESSION, SLOT_1500)).is_file(), "the school's counts never wait on the step"
        assert len(alerts) == 1 and "instructor not run" in alerts[0] and "51200" not in alerts[0]
        assert ("KeyError" if name == "broken" else "time limit") in alerts[0]


def test_an_instructor_finishing_after_its_limit_has_nothing_committed_and_the_alert_says_time_limit(clone):  # noqa: F811
    """The orchestrator's test (judge 523): the late work's writes are dropped with it, never run, never committed."""
    alerts = []
    counts = SessionCounts(clone, SessionFilesCommitter(clone, "Counts: {what}"), lambda session: (INSTRUCTOR_FILE,))
    StagedSessionStep("instructor", writing(clone, delay=0.3), alerts.append, seconds=0.05)(b.SESSION)
    counts.write(b.SESSION, SLOT_1500, (), ())  # the run's single commit, while the work still sleeps
    time.sleep(0.5)  # the work has now finished on its own
    tracked = set(git(clone, "ls-tree", "-r", "--name-only", "origin/main").split())
    assert str(counts_path(b.SESSION, SLOT_1500)) in tracked
    assert INSTRUCTOR_FILE not in tracked and not (clone / INSTRUCTOR_FILE).exists(), "a late write ran"
    assert git(clone, "status", "--porcelain").strip() == ""
    assert len(alerts) == 1 and "instructor not run" in alerts[0] and "time limit" in alerts[0]


def test_an_instructor_in_time_is_written_on_the_run_s_thread_and_taken_by_the_one_commit(clone):  # noqa: F811
    seen, alerts = [], []
    counts = SessionCounts(clone, SessionFilesCommitter(clone, "Counts: {what}"), lambda session: (INSTRUCTOR_FILE,))
    before = int(git(clone, "rev-list", "--count", "origin/main"))
    StagedSessionStep("instructor", writing(clone, seen=seen), alerts.append)(b.SESSION)
    counts.write(b.SESSION, SLOT_1500, (), ())
    assert seen == [threading.get_ident()] and alerts == []
    assert int(git(clone, "rev-list", "--count", "origin/main")) == before + 1, "one commit takes both"
    assert INSTRUCTOR_FILE in git(clone, "ls-tree", "-r", "--name-only", "origin/main").split()


def test_a_failing_write_or_prepare_alerts_by_class_and_the_work_never_runs_after_a_failed_prepare():
    def failing_writes(session):
        def writes():
            raise PermissionError("receipts/data/school/instructor/2026/10/22.causes")

        return writes

    def refused():
        raise subprocess.CalledProcessError(128, "git fetch")

    alerts, ran = [], []
    StagedSessionStep("instructor", failing_writes, alerts.append)(b.SESSION)
    StagedSessionStep("instructor", lambda session: ran.append(session), alerts.append, prepare=refused)(b.SESSION)
    assert ran == [] and len(alerts) == 2
    assert "instructor not written" in alerts[0] and "PermissionError" in alerts[0] and "2026/10" not in alerts[0]
    assert "instructor not run" in alerts[1] and "CalledProcessError" in alerts[1]


def test_prepare_runs_on_the_run_s_thread_before_the_work(clone):  # noqa: F811
    order = []
    work = lambda session: order.append(("work", threading.get_ident())) or (lambda: None)  # noqa: E731
    step = StagedSessionStep("instructor", work, [].append, prepare=lambda: order.append(("prepare",
                             threading.get_ident())))  # fmt: skip
    step(b.SESSION)
    assert [name for name, _ in order] == ["prepare", "work"]
    assert order[0][1] == threading.get_ident() != order[1][1]


def test_a_rerun_of_a_complete_session_runs_the_step_again_before_committing(tmp_path):
    calls = []
    rig = rig_with(tmp_path, calls.append)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert calls == [b.SESSION, b.SESSION]
