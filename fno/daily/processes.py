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
from collections.abc import Callable, Sequence
from pathlib import Path

from ..alerts.sender import NOT_SENT, SENT

UNSENT = NOT_SENT.split(":")[0]  # "alert NOT sent": a child's own unsent alert, printed for the routine's connector
OWN_ALERT = (SENT, UNSENT)  # a line a command's own alert left, sent or not
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

    @abstractmethod
    def alerted(self) -> bool:
        """Whether the command sent, or tried to send, its own alert: over its whole output, since the kept lines
        never hold an unsent alert (they reach the committed run record)."""


class Processes(ABC):
    @abstractmethod
    def start(self, arguments: Sequence[str]) -> Process:
        """Starts `python -m fno <arguments>` in the repository and returns at once."""


class ChildProcess(Process):
    """Its whole output is read once when it ends or is stopped: every unsent-alert line in it is printed as written
    (judge 178 addendum 6: CLAUDE.md's 3 pm rules have the routine post those lines), the last lines are kept."""

    def __init__(self, popen: subprocess.Popen, output, report: Callable[[str], None] = print):
        self.popen, self.output, self.report, self.printed = popen, output, report, None

    def poll(self) -> int | None:
        return self.popen.poll()

    def stop(self) -> None:
        """Kills the child's whole process group, so a git or Groww call it started dies with it (judge 178 add. 3
        note 8)."""
        with contextlib.suppress(ProcessLookupError):  # it ended on its own meanwhile
            os.killpg(self.popen.pid, signal.SIGKILL)
        self.popen.wait()
        self._read()

    def lines(self) -> list[str]:
        """The last result lines, never an unsent alert: its text goes to the routine only (it can hold what is meant
        for Slack alone, such as a Drive error's text), never into the committed run record."""
        return [line for line in self._read() if UNSENT not in line][-KEPT_LINES:]

    def alerted(self) -> bool:
        return printed_an_alert(self._read())

    def _read(self) -> list[str]:
        if self.printed is None:
            self.output.seek(0)
            self.printed = [line.rstrip() for line in self.output.read().splitlines() if line.strip()]
            self.output.close()
            for line in self.printed:
                if UNSENT in line:
                    self.report(line)
        return self.printed


class ChildProcesses(Processes):
    """The commands run with this Python and the routine's environment (its settings, never printed)."""

    def __init__(self, root: Path, report: Callable[[str], None] = print):
        self.root, self.report = Path(root), report

    def start(self, arguments: Sequence[str]) -> Process:
        output = tempfile.TemporaryFile("w+", encoding="utf-8")  # noqa: SIM115 - open for the child's run, closed once read
        command = [sys.executable, "-m", "fno", *arguments]
        # its own process group, so `stop` ends everything it started
        popen = subprocess.Popen(command, cwd=self.root, stdout=output, stderr=subprocess.STDOUT, text=True,
                                 start_new_session=True)  # fmt: skip
        return ChildProcess(popen, output, self.report)


def printed_an_alert(printed: Sequence[str]) -> bool:
    """One rule for every `Process`: a line left by the command's own alert, sent or not."""
    return any(mark in line for line in printed for mark in OWN_ALERT)
