"""The paper desk's daily run (story E3, design 13.5 steps 4-5): `DailyRun.run(day)` walks the fixed timetable.

1. On a day that is not a recorded session (A7 calendar: closed, or a muhurat-only evening) nothing runs.
2. `versions`: Book 1's D6 version is kept current before any decision (judge 80).
3. `pack` (from about 14:58): E2's common pack, built only once the 3 pm canonical snapshot is committed (judge 72),
   retried until the recorder's window ends.
4. `decisions` (at the deadline): each book's decision committed by then; a book without one gets a committed
   "no decision (late)" and cannot join later. A slow book delays nothing: decisions are read, not awaited.
5. `snapshot` (at the execution time): one capture for every book, with one common retry if it is not valid.
6. `fills`: every timely decision with a completed C4 pass fills against that one snapshot; none if it is invalid.
7. `exits`: every book's exit review, whatever happened before (risk-reducing exits always run).

Each step's start, end, inputs and result go to `journal/runs/<date>.json`, committed after the step; a restarted run
skips every step already recorded, so nothing is done twice.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta
from pathlib import Path

from ..quotes.recorder import RECORDED_SESSION_KINDS
from ..research_data.calendar import SessionCalendar
from .daily_ports import Committer, Waiter
from .daily_steps import DeskSteps, StepOutcome
from .run_log import RunLog

SKIPPED = "skipped"
PACK_RETRY = timedelta(seconds=30)


class DailyRun:
    def __init__(self, steps: DeskSteps, calendar: SessionCalendar, committer: Committer, waiter: Waiter,
                 clock: Callable[[], datetime]):  # fmt: skip
        self.steps, self.calendar, self.committer, self.waiter, self.clock = steps, calendar, committer, waiter, clock

    def run(self, day: date) -> RunLog:
        log = RunLog.open(self.steps.root, day)
        kind = self.calendar.session_kind(day)
        if kind not in RECORDED_SESSION_KINDS:
            if not log.done(SKIPPED):
                self._step(log, SKIPPED, lambda: StepOutcome({"session": kind}, {"reason": "not a session day"}))
            return log
        times, steps = self.steps.timetable, self.steps
        plan = (
            ("versions", times.pack, lambda: steps.keep_versions(day)),
            ("pack", times.pack, lambda: self._pack(day)),
            ("decisions", times.decision_deadline, lambda: steps.collect_decisions(day)),
            ("snapshot", times.execution_snapshot, lambda: steps.take_snapshot(day)),
            ("fills", times.execution_snapshot, lambda: steps.fill(day, log.result("snapshot")["valid"])),
            ("exits", times.execution_snapshot, lambda: steps.review_exits(day)),
        )
        for name, moment, action in plan:
            if not log.done(name):
                self.waiter.until(times.at(day, moment))
                self._step(log, name, action)
        return log

    def _pack(self, day: date) -> StepOutcome:
        """Retries while the canonical snapshot is not committed yet, until the recorder's window ends."""
        last = self.steps.timetable.at(day, self.steps.timetable.pack_wait_until)
        outcome = self.steps.build_pack(day)
        while not outcome.result["built"] and self.clock() + PACK_RETRY <= last:
            self.waiter.until(self.clock() + PACK_RETRY)
            outcome = self.steps.build_pack(day)
        return outcome

    def _step(self, log: RunLog, name: str, action: Callable[[], StepOutcome]) -> None:
        started = self.clock()
        outcome = action()
        log.record(name, started, self.clock(), outcome.inputs, outcome.result)
        paths: tuple[Path, ...] = (log.path, *outcome.paths)
        self.committer.commit(paths, f"Desk run {log.day} step {name}")
