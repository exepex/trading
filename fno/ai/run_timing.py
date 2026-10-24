"""An AI book run's own timing (story F8c; BG1's self-timed record, `fno/budget/self_timed.py`), taken inside the steps
the routine already runs, so today's prompts (frozen by hash) need no new step: `brief` notes the start (per day and
book) and the routine's session id, and `reveal`, after its own publish, publishes `timing_path(day, book)`. Each book
publishes only its own file (both reveal at 15:15:10, so two appends to one ledger would race); `ai collect` folds
every file into the usage ledger. Standard library only, like every step the routine runs."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .book_run import BookRun
from .paths import WORK_FOLDER, timing_path
from .transport import SubmissionTransport

STARTED_FILE = "started_{day}_{book}.json"  # per run: a reused container never lends one day's start to another
NO_START = "no start was noted (brief did not run in this session)"
NO_SESSION = "no session id: the routine's environment has no CLAUDE_CODE_REMOTE_SESSION_ID"
REMOTE_PREFIX, SESSION_PREFIX = "cse_", "session_"


def routine_session_id(remote_id: str) -> str:
    """The session tools' name for this session: the environment's `cse_<id>` is `session_<id>`."""
    remote_id = remote_id.strip()
    return SESSION_PREFIX + remote_id.removeprefix(REMOTE_PREFIX) if remote_id else ""


@dataclass
class RunTiming:
    root: Path
    transport: SubmissionTransport
    clock: Callable[[], datetime]
    session_id: str  # empty outside a cloud session: the start is noted, the publish refused

    def _started(self, pointer: BookRun) -> Path:
        return self.root / WORK_FOLDER / STARTED_FILE.format(day=pointer.day.isoformat(), book=pointer.book)

    def start(self, pointer: BookRun) -> None:
        """The run's start, kept from its first `brief` (a repeated brief is the same run)."""
        path = self._started(pointer)
        if not path.is_file():
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps({"started_at": self.clock().isoformat()}), encoding="utf-8")

    def publish(self, pointer: BookRun, message: str) -> str:
        """Publishes the run's timing once; the line to print. A ValueError says why it cannot be published."""
        started_file = self._started(pointer)
        if not started_file.is_file():
            raise ValueError(NO_START)
        if not self.session_id:
            raise ValueError(NO_SESSION)
        path = timing_path(pointer.day, pointer.book)
        if self.transport.existing(path) is not None:
            return f"timing already published: {path}"
        started = json.loads(started_file.read_text(encoding="utf-8"))["started_at"]
        timing = {"session_id": self.session_id, "model": "", "started_at": started,
                  "ended_at": self.clock().isoformat()}  # fmt: skip
        commit = self.transport.publish(path, json.dumps(timing, indent=1) + "\n", message)
        return f"timed: {pointer.book} {pointer.day} from {started} to {timing['ended_at']} in commit {commit[:10]}"
