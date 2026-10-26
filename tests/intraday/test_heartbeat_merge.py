"""Story A16 heartbeat fix (26 Oct 2026, judge 691): two overlapping runs push the heartbeat. The pull's `-X theirs`
keeps what is already on GitHub, and the run that lost a mark's claim pushes first. The taker's mark fields live in
their own file that a run taking no mark never rewrites, so they are never thrown away or mixed with another beat."""

import json

import pytest

from fno.intraday.heartbeat import Heartbeat
from fno.intraday.wiring import OWNED_PATHS
from fno.storage.owned_paths_commit import OwnedPathsCommitter
from tests.intraday.test_two_clones import FOLDER, clone, git

OLD_MARK = {"clock_skew_seconds": 0.0, "clock_status": "clock_ok", "mark": "15:30", "session": "2026-10-23",
            "status": "good"}  # fmt: skip
NEW_MARK = {**OLD_MARK, "mark": "09:30", "session": "2026-10-26"}
NAME = "story A16 intraday recorder"


def committer(checkout):
    return OwnedPathsCommitter(checkout, checkout / FOLDER, OWNED_PATHS, message="Data: intraday slots ({what})",
                               label="intraday files", keep_remote_on_conflict=True)  # fmt: skip


def push_run(checkout, started, finished, mark=None):
    beat = Heartbeat(checkout / FOLDER)
    beat.write_run(started, finished, NAME)
    if mark:
        beat.write_mark(mark)
    assert "committed and pushed" in committer(checkout).commit("test")


@pytest.mark.parametrize("taker_pushes_first", [False, True])
def test_the_taker_keeps_its_mark_whichever_overlapping_run_pushes_first(tmp_path, taker_pushes_first):
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    seed = clone(tmp_path, origin, "seed")
    (seed / FOLDER).mkdir(parents=True)
    old = Heartbeat(seed / FOLDER)
    old.write_run("2026-10-23T09:45:58+00:00", "2026-10-23T10:00:53+00:00", NAME)
    old.write_mark(OLD_MARK)
    git(seed, "add", "-A")
    git(seed, "commit", "-q", "-m", "start")
    git(seed, "push", "-q", "origin", "HEAD:main")
    no_mark, took_mark = clone(tmp_path, origin, "run-a"), clone(tmp_path, origin, "run-b")
    loser = ("2026-10-26T03:45:24+00:00", "2026-10-26T03:59:21+00:00")  # lost the claim: run times only
    taker = ("2026-10-26T03:46:08+00:00", "2026-10-26T04:01:02+00:00", NEW_MARK)

    for first in [taker, loser] if taker_pushes_first else [loser, taker]:
        push_run(took_mark if first is taker else no_mark, *first)

    git(seed, "pull", "-q", "origin", "main")
    published = Heartbeat(seed / FOLDER).read()
    assert (published["session"], published["mark"]) == ("2026-10-26", "09:30")  # 26 Oct's order: loser first
    runs = json.loads((seed / FOLDER / "heartbeat.json").read_text())
    assert set(runs) == {"recorder", "run_started_at", "run_finished_at"}  # whole beats of one run each
    assert (runs["run_started_at"], runs["run_finished_at"]) in (loser, taker[:2])
    assert not git(took_mark, "status", "--porcelain") and not git(no_mark, "status", "--porcelain")
