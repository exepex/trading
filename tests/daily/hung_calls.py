"""A git run for tests of the hard limit (story O2): the short limit for the hung call only, counted from the moment
its hook runs (it has written its pid, so git holds its lock). Every other call keeps the run's own limit, so neither
a slow `git add` nor git's own start on a loaded machine can meet the short limit (judge E, 22 Oct: a flake in a full
parallel run; reproduced with every git call slowed past the limit)."""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from fno.desk.git_limit import GIT_CALL_LIMIT_SECONDS, LimitedRun

from .fakes import QuietLocks

HOOK_START_WAIT = 120.0  # how long a loaded machine may take to reach the hook; a test error past it, never a pass


class HungCallRun(LimitedRun):
    """`calls`: how many calls of `name` hang (None: every one); `when`: whether the hook hangs right now."""

    def __init__(self, name: str, pid_file: Path, calls: int | None = None, when: Callable[[], bool] = lambda: True,
                 locks=QuietLocks):  # fmt: skip
        super().__init__(locks, started=self._wait_for_hook)
        self.name, self.pid_file, self.calls, self.when = name, pid_file, calls, when
        self.hook_at, self.waiting = None, False

    def __call__(self, command, *, timeout, **options):
        hung = self.waiting = self.name in command and self.calls != 0 and self.when()
        if hung:
            self.pid_file.unlink(missing_ok=True)  # this call's hook writes it afresh
            self.calls = None if self.calls is None else self.calls - 1
        return super().__call__(command, timeout=timeout if hung else GIT_CALL_LIMIT_SECONDS, **options)

    def _wait_for_hook(self, command) -> None:
        if not self.waiting:
            return
        deadline = time.monotonic() + HOOK_START_WAIT
        while not (self.pid_file.is_file() and self.pid_file.read_text().strip()):
            assert time.monotonic() < deadline, f"the {self.name} hook never started"
            time.sleep(0.01)
        self.hook_at = time.monotonic()
