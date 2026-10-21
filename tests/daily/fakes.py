"""Story O1 fakes: commands that end at a set time, a committer that records what each commit holds and when, and
O1 steps that record their calls. Never the network, never a real child process."""

from __future__ import annotations

import os
from datetime import datetime

from fno.constants import STEP_OK
from fno.daily.earlier_run import PartMarkers
from fno.daily.part_locks import PART_LOCKS, PartLocks
from fno.daily.processes import UNSENT, Process, Processes, alerted_in
from fno.daily.quote_parts import QUOTE_PARTS, QuoteParts
from fno.daily.quote_steps import ServicingWaiter
from fno.desk.daily_ports import CommitFailed, Committer, DayStep
from fno.desk.daily_steps import StepOutcome
from fno.desk.git_limit import GitLocks
from tests.timetable.fakes import Clock


class QuietLocks(GitLocks):
    """No other git process runs (story O2): the test machine's xdist workers run git calls that must not count."""

    def _git_alive(self) -> bool:
        return False


class FakeProcess(Process):
    """Holds the part's lock it was handed (its own copy, as a child inherits it) until it ends or is stopped."""

    def __init__(self, clock: Clock, ends_at: datetime, code: int, lines: list[str], hold: int | None = None):
        self.clock, self.ends_at, self.code, self.printed, self.stopped = clock, ends_at, code, lines, False
        self.lock = None if hold is None else os.dup(hold)

    def poll(self) -> int | None:
        if self.clock() < self.ends_at or self.stopped:
            return None
        self._release()
        return self.code

    def _release(self) -> None:
        if self.lock is not None:
            os.close(self.lock)
            self.lock = None

    def lines(self) -> list[str]:
        return [line for line in self.printed if UNSENT not in line]  # as ChildProcess keeps them

    def alerted(self) -> bool:
        return alerted_in(self.printed)

    def stop(self) -> None:
        self.stopped = True
        self._release()


class FakeProcesses(Processes):
    """`script[arguments] = (ends_at, code, lines)`; records each start with the clock's time."""

    def __init__(self, clock: Clock, script: dict):
        self.clock, self.script, self.started, self.made = clock, script, [], {}

    def start(self, arguments, hold=None) -> Process:
        ends_at, code, lines = self.script[tuple(arguments)]
        self.started.append((self.clock(), tuple(arguments)))
        self.made[tuple(arguments)] = FakeProcess(self.clock, ends_at, code, lines, hold)
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


class FakeMarkers(PartMarkers):
    """`recorded[part name]`: the commit holding that part's canonical markers; a part not in it has none."""

    def __init__(self, recorded: dict | None = None):
        self.by_canonicals = {part.canonicals: commit for part in QUOTE_PARTS
                              for name, commit in (recorded or {}).items() if part.name == name}  # fmt: skip

    def missing(self, day, canonicals):
        return [] if canonicals in self.by_canonicals else [f"{stem}.canonical" for _, stem in canonicals]

    def recorded(self, day, canonicals):
        return self.by_canonicals.get(canonicals)


def tracking(folder, recorded: dict | None = None) -> tuple[PartLocks, FakeMarkers]:
    """The parts' real locks in `folder` (one container: shared by a run and its rerun) and fake markers."""
    return PartLocks(folder / PART_LOCKS), FakeMarkers(recorded)


def quote_parts(clock, script, committer, alerts, files=None, folder=None, recorded=None):
    parts = QuoteParts(QUOTE_PARTS, FakeProcesses(clock, script), committer, part_files(files or {}), alerts, clock,
                       *tracking(folder, recorded))  # fmt: skip
    return parts, ServicingWaiter(parts, clock, sleep=clock.advance)
