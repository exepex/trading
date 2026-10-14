"""Story D3 criteria 3 and 5: a writer killed mid-way leaves the whole run or none; a run committed at or after the
day's execution snapshot is late and is never filled."""

import os
import subprocess
import sys
from datetime import datetime

import pytest

from fno.config import ROOT
from fno.models import IST
from fno.playbook.decision_run import replay
from fno.playbook.decision_store import DecisionStore
from fno.playbook.decision_timing import LATE, ON_TIME, LateDecision, require_on_time, timeliness
from fno.playbook.history import PlaybookGit
from tests.playbook.builders import git
from tests.playbook.evaluation_builders import DAY, evaluator

from .builders import SAME_CODE, doc, run_day, snapshot

KILL_ON_THIRD_FILE = """
import os, pathlib, sys
from tests.decisions.builders import doc, run_day, snapshot
written = []
original = pathlib.Path.write_bytes
def dying_write(self, data):
    written.append(self)
    if len(written) == 3:
        os._exit(9)  # the process dies between two files of the run
    return original(self, data)
pathlib.Path.write_bytes = dying_write
run_day(pathlib.Path(sys.argv[1]), snapshot(doc("sc-a"), doc("sc-b")))
"""


def test_a_writer_killed_mid_way_leaves_no_run_and_the_next_run_is_whole(tmp_path):
    killed = subprocess.run([sys.executable, "-c", KILL_ON_THIRD_FILE, str(tmp_path)], cwd=ROOT,
                            env={**os.environ, "PYTHONPATH": str(ROOT)}, capture_output=True, text=True)  # fmt: skip
    assert killed.returncode == 9, killed.stderr
    store = DecisionStore(tmp_path, "book1_rules")
    assert store.runs(DAY) == []  # only a hidden temporary folder may remain, never a partial run
    assert [p.name for p in store.day_folder(DAY).iterdir()] == [".2026-10-13-r1.tmp"]
    run = run_day(tmp_path, snapshot(doc("sc-a"), doc("sc-b")))
    assert run.name == "2026-10-13-r1" and store.edited(run) == [] and replay(run, evaluator(), SAME_CODE) == []
    assert not (store.day_folder(DAY) / ".2026-10-13-r1.tmp").exists()


SNAPSHOT_AT = datetime(2026, 10, 13, 15, 15, tzinfo=IST)


def commit_at(root, moment: str) -> None:
    git(root, "add", "-A")
    env = {**os.environ, "GIT_COMMITTER_DATE": moment, "GIT_AUTHOR_DATE": moment}
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "decisions"],
                   cwd=root, env=env, check=True)  # fmt: skip


@pytest.mark.parametrize(
    ("moment", "expected"),
    [("2026-10-13T15:12:00+05:30", ON_TIME), ("2026-10-13T15:15:00+05:30", LATE), ("2026-10-13T15:20:00+05:30", LATE)],
)
def test_a_run_is_on_time_only_if_committed_before_the_execution_snapshot(tmp_path, moment, expected):
    git(tmp_path, "init", "-q")
    run = run_day(tmp_path, snapshot(doc("sc-a")))
    commit_at(tmp_path, moment)
    status, why = timeliness(run, tmp_path, SNAPSHOT_AT, PlaybookGit(tmp_path))
    assert status == expected and "15:15" in why
    if expected == LATE:
        with pytest.raises(LateDecision, match="never filled"):
            require_on_time(run, tmp_path, SNAPSHOT_AT, PlaybookGit(tmp_path))


def test_an_uncommitted_run_is_late(tmp_path):
    git(tmp_path, "init", "-q")
    run = run_day(tmp_path, snapshot(doc("sc-a")))
    assert timeliness(run, tmp_path, SNAPSHOT_AT, PlaybookGit(tmp_path)) == (LATE, "not committed")
