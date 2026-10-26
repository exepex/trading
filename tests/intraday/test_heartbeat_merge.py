"""Story A16 heartbeat fix (26 Oct 2026): two overlapping runs push `heartbeat.json`; the pull's `-X theirs` settles a
clash per hunk, and a pretty-printed file has one line per field, so the merge once kept the first run's `mark` with
the other run's `session` and times (session 2026-10-23 beside mark 09:30 on 26 Oct). One line per beat: a clash is
settled for the whole file, so the heartbeat is always one run's own beat."""

import json
import subprocess

from fno.intraday.heartbeat import Heartbeat
from fno.intraday.wiring import OWNED_PATHS
from fno.storage.owned_paths_commit import OwnedPathsCommitter
from tests.intraday.test_two_clones import FOLDER, clone, git

OLD = {"clock_skew_seconds": 0.0, "clock_status": "clock_ok", "mark": "15:30",
       "recorder": "story A16 intraday recorder", "run_finished_at": "2026-10-23T10:00:53+00:00",
       "run_started_at": "2026-10-23T09:45:58+00:00",
       "session": "2026-10-23", "status": "good"}  # fmt: skip


def committer(checkout):
    return OwnedPathsCommitter(checkout, checkout / FOLDER, OWNED_PATHS, message="Data: intraday slots ({what})",
                               label="intraday files", keep_remote_on_conflict=True)  # fmt: skip


def push_beat(checkout, beat):
    Heartbeat(checkout / FOLDER).write(beat)
    assert "committed and pushed" in committer(checkout).commit("test")


def test_overlapping_runs_never_leave_a_heartbeat_mixed_from_two_beats(tmp_path):
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    seed = clone(tmp_path, origin, "seed")
    (seed / FOLDER).mkdir(parents=True)
    Heartbeat(seed / FOLDER).write(OLD)
    git(seed, "add", "-A")
    git(seed, "commit", "-q", "-m", "start")
    git(seed, "push", "-q", "origin", "HEAD:main")
    no_mark, took_mark = clone(tmp_path, origin, "run-a"), clone(tmp_path, origin, "run-b")
    new = {**OLD, "mark": "09:30", "session": "2026-10-26", "run_started_at": "2026-10-26T03:46:08+00:00",
           "run_finished_at": "2026-10-26T04:01:02+00:00"}  # fmt: skip
    only_times = {**OLD, "run_started_at": "2026-10-26T03:45:24+00:00", "run_finished_at": "2026-10-26T03:59:21+00:00"}

    push_beat(no_mark, only_times)  # the run that took no mark: the old session's fields, new run times
    push_beat(took_mark, new)  # the run that took 09:30: its pull meets the first run's heartbeat

    git(seed, "pull", "-q", "origin", "main")
    published = json.loads((seed / FOLDER / "heartbeat.json").read_text())
    assert published in (new, only_times)  # one run's whole beat, never a mix
    assert not git(took_mark, "status", "--porcelain")
    assert subprocess.run(["git", "diff", "--check"], cwd=seed).returncode == 0
