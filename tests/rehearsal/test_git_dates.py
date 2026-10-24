"""REH1b: every git call of a rehearsal goes through its shim and is dated by the replay clock, so D3's late rule and
G13b's seals see the replayed day's times, not the wall clock's."""

import os
import subprocess
from datetime import UTC, datetime

from fno.rehearsal.clock import ReplayClock
from fno.rehearsal.git_dates import install_git_shim


def test_a_commit_through_the_shim_is_dated_by_the_replay_clock(tmp_path):
    replay = datetime(2026, 10, 23, 9, 42, tzinfo=UTC)  # 15:12 IST, the decision deadline
    ReplayClock(tmp_path / "state").start(replay)
    env = {**os.environ, "PATH": install_git_shim(tmp_path / "bin", tmp_path / "state")}
    for name in ("GIT_COMMITTER_DATE", "GIT_AUTHOR_DATE"):
        env.pop(name, None)
    repo = tmp_path / "repo"

    def git(*args):
        return subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True, text=True).stdout

    repo.mkdir()
    git("init", "-q")
    git("-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "decision")
    dates = git("log", "-1", "--format=%ct %at").split()
    assert all(abs(int(d) - replay.timestamp()) <= 5 for d in dates)
    assert git("--version").startswith("git version")  # the real git runs behind it
