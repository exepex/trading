"""Story O1 fakes: commands that end at a set time, a committer that records what each commit holds and when, and
O1 steps that record their calls. Never the network, never a real child process."""

from __future__ import annotations

from datetime import datetime

from fno.constants import STEP_OK
from fno.daily.processes import Process, Processes
from fno.daily.quote_parts import QUOTE_PARTS, QuoteParts
from fno.daily.quote_steps import ServicingWaiter
from fno.desk.daily_ports import CommitFailed, Committer, DayStep
from fno.desk.daily_steps import StepOutcome
from tests.timetable.fakes import Clock


class FakeProcess(Process):
    def __init__(self, clock: Clock, ends_at: datetime, code: int, lines: list[str]):
        self.clock, self.ends_at, self.code, self.printed, self.stopped = clock, ends_at, code, lines, False

    def poll(self) -> int | None:
        return self.code if self.clock() >= self.ends_at else None

    def lines(self) -> list[str]:
        return list(self.printed)

    def stop(self) -> None:
        self.stopped = True


class FakeProcesses(Processes):
    """`script[arguments] = (ends_at, code, lines)`; records each start with the clock's time."""

    def __init__(self, clock: Clock, script: dict):
        self.clock, self.script, self.started, self.made = clock, script, [], {}

    def start(self, arguments) -> Process:
        ends_at, code, lines = self.script[tuple(arguments)]
        self.started.append((self.clock(), tuple(arguments)))
        self.made[tuple(arguments)] = FakeProcess(self.clock, ends_at, code, lines)
        return self.made[tuple(arguments)]


class RecordingCommitter(Committer):
    def __init__(self, clock: Clock, log: list, fail_on: str = ""):
        self.clock, self.log, self.fail_on = clock, log, fail_on

    def commit(self, paths, message, own_unpushed=None):
        if self.fail_on and self.fail_on in message:
            raise CommitFailed(f"push of '{message}' rejected 3 times", unpushed=True)
        self.log.append((self.clock(), message, tuple(str(p) for p in paths)))
        return f"c{len(self.log)}"


class RecordedStep(DayStep):
    def __init__(self, name: str, calls: list, result: dict | None = None, raises: Exception | None = None):
        self.name, self.calls, self.result, self.raises = name, calls, result, raises

    def run(self, day):
        self.calls.append(self.name)
        if self.raises:
            raise self.raises
        return StepOutcome({}, self.result or {"status": STEP_OK, "reason": f"{self.name} done"})


def part_files(spec_files: dict):
    """`changed` for the parts: each part's own files, by its first pathspec."""
    return lambda specs: list(spec_files.get(specs[0], []))


def quote_parts(clock, script, committer, alerts, files=None):
    parts = QuoteParts(QUOTE_PARTS, FakeProcesses(clock, script), committer, part_files(files or {}), alerts, clock)
    return parts, ServicingWaiter(parts, clock, sleep=clock.advance)
