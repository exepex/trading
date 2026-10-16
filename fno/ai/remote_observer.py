"""The remote observer (story F1t): a child process that reads the remote branch's head at each deadline and appends the
reading to an observation file, so the readings never depend on what the caller's thread is doing (a slow step before
the collection cannot move them). It only asks the remote (`git ls-remote`), which never touches the checkout, so the
caller's rule "git in the repository only in the run's thread" holds. Each reading is bounded by `LS_REMOTE_SECONDS`;
a failure is written as a failed reading, never retried later (a late reading proves nothing).

    python -m fno.ai.remote_observer --out <file> --deadline <ISO time> [--deadline <ISO time> ...]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path

from ..models import now_ist
from .observed_receipts import Observation, ObservationFile

LS_REMOTE_SECONDS = 20
REMOTE, BRANCH = "origin", "refs/heads/main"


class RemoteHeadFailed(RuntimeError):
    """The remote's head could not be read; the message says why."""


class RemoteHead(ABC):
    @abstractmethod
    def head(self) -> str:
        """The commit the remote branch points to now."""


class GitLsRemote(RemoteHead):
    def __init__(self, root: Path, remote: str = REMOTE, branch: str = BRANCH):
        self.root, self.remote, self.branch = Path(root), remote, branch

    def head(self) -> str:
        try:
            done = subprocess.run(["git", "ls-remote", self.remote, self.branch], cwd=self.root, capture_output=True,
                                  text=True, timeout=LS_REMOTE_SECONDS)  # fmt: skip
        except subprocess.TimeoutExpired:
            raise RemoteHeadFailed(f"git ls-remote took over {LS_REMOTE_SECONDS} s") from None
        fields = done.stdout.split()
        if done.returncode != 0 or len(fields) < 2 or fields[1] != self.branch:
            raise RemoteHeadFailed(f"git ls-remote failed: {(done.stderr or done.stdout).strip()[-200:]}")
        return fields[0]


class RemoteObserver:
    def __init__(self, remote: RemoteHead, out: ObservationFile, clock: Callable[[], datetime],
                 sleep: Callable[[float], None]):  # fmt: skip
        self.remote, self.out, self.clock, self.sleep = remote, out, clock, sleep

    def run(self, deadlines: Sequence[datetime]) -> None:
        for deadline in sorted(deadlines):
            wait = (deadline - self.clock()).total_seconds()
            if wait > 0:
                self.sleep(wait)
            started = self.clock()
            try:
                commit, error = self.remote.head(), ""
            except RemoteHeadFailed as failed:
                commit, error = None, str(failed)
            self.out.append(Observation(deadline, started, self.clock(), commit, error))


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m fno.ai.remote_observer")
    parser.add_argument("--out", type=Path, required=True, help="the observation file (git-ignored)")
    parser.add_argument("--deadline", type=datetime.fromisoformat, action="append", required=True)
    args = parser.parse_args(argv)
    if any(d.tzinfo is None for d in args.deadline):
        print("refused: every deadline needs its time zone")
        return 1
    RemoteObserver(GitLsRemote(root or Path.cwd()), ObservationFile(args.out), now_ist, time.sleep).run(args.deadline)
    return 0


if __name__ == "__main__":
    sys.exit(main())
