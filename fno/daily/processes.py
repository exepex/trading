"""The daily run's child commands (story O1): each of its own steps is an existing `python -m fno ...` command run
unchanged, so its rules, output and alerts stay the story's that built it. Behind an interface so tests use fakes."""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path

KEPT_LINES = 10  # the run log keeps the last lines a command printed (result lines; never a secret, O5's scan)


class Process(ABC):
    @abstractmethod
    def poll(self) -> int | None:
        """The exit code once the command has ended; None while it runs."""

    @abstractmethod
    def lines(self) -> list[str]:
        """The last `KEPT_LINES` non-empty lines it printed (read once, after it has ended)."""

    @abstractmethod
    def stop(self) -> None:
        """Ends a command that ran past its limit."""


class Processes(ABC):
    @abstractmethod
    def start(self, arguments: Sequence[str]) -> Process:
        """Starts `python -m fno <arguments>` in the repository and returns at once."""


class ChildProcess(Process):
    def __init__(self, popen: subprocess.Popen, output):
        self.popen, self.output = popen, output

    def poll(self) -> int | None:
        return self.popen.poll()

    def stop(self) -> None:
        """Kills the child's whole process group, so a git or Groww call it started dies with it (judge 178 add. 3
        note 8)."""
        with contextlib.suppress(ProcessLookupError):  # it ended on its own meanwhile
            os.killpg(self.popen.pid, signal.SIGKILL)
        self.popen.wait()

    def lines(self) -> list[str]:
        self.output.seek(0)
        printed = self.output.read()
        self.output.close()
        return [line.rstrip() for line in printed.splitlines() if line.strip()][-KEPT_LINES:]


class ChildProcesses(Processes):
    """The commands run with this Python and the routine's environment (its settings, never printed)."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def start(self, arguments: Sequence[str]) -> Process:
        output = tempfile.TemporaryFile("w+", encoding="utf-8")  # noqa: SIM115 - open for the child's run, closed by lines()
        command = [sys.executable, "-m", "fno", *arguments]
        # its own process group, so `stop` ends everything it started
        popen = subprocess.Popen(command, cwd=self.root, stdout=output, stderr=subprocess.STDOUT, text=True,
                                 start_new_session=True)  # fmt: skip
        return ChildProcess(popen, output)
