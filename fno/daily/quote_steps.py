"""The quote parts as the daily run's steps (story O1): `quotes` starts them and goes on; `quotes_done`, after the
desk's exits, waits for those still running and records each part's result line and commit. `ServicingWaiter` is
the desk's waiter that commits a part as soon as it ends, while the desk waits for its next time."""

from __future__ import annotations

import time as clock_time
from collections.abc import Callable
from datetime import date, datetime

from ..constants import STEP_FAILED, STEP_OK
from ..desk.daily_ports import DayStep, Waiter
from ..desk.daily_steps import StepOutcome
from .quote_parts import QuoteParts

POLL_SECONDS = 5.0
NOT_IN_THIS_RUN = "the parts were started by an earlier run that ended; their results are in the recorder's own files"
NOT_IN_THIS_RUN_ALERT = (
    "F&O daily run {day}: the 3 pm quote parts were started by an earlier run that ended: check each part's canonical "
    "marker, and commit any part file left with the `git add` lines of CLAUDE.md's Daily desk routine"
)


class ServicingWaiter(Waiter):
    def __init__(
        self, parts: QuoteParts, now: Callable[[], datetime], sleep: Callable[[float], None] = clock_time.sleep
    ):
        self.parts, self.now, self.sleep = parts, now, sleep

    def until(self, moment: datetime) -> None:
        self.parts.service()
        while (left := (moment - self.now()).total_seconds()) > 0:
            self.sleep(min(POLL_SECONDS, left))
            self.parts.service()


class StartQuoteParts(DayStep):
    def __init__(self, parts: QuoteParts):
        self.parts = parts

    def run(self, day: date) -> StepOutcome:
        started = self.parts.start(day)
        waiting = [f"{p.name} after {p.starts_after}" for p in self.parts.parts if p.starts_after]
        reason = f"started {', '.join(started)}" + (f"; {', '.join(waiting)}" if waiting else "")
        return StepOutcome({"parts": [p.name for p in self.parts.parts]}, {"status": STEP_OK, "reason": reason})


class FinishQuoteParts(DayStep):
    def __init__(self, parts: QuoteParts, waiter: Waiter):
        self.parts, self.waiter = parts, waiter

    def run(self, day: date) -> StepOutcome:
        if not self.parts.started:  # alerted: a failure here is never silent (O2, owner 16 Oct)
            self.parts.alerts.send(NOT_IN_THIS_RUN_ALERT.format(day=day))
            return StepOutcome({}, {"status": STEP_FAILED, "reason": NOT_IN_THIS_RUN})
        results = self.parts.finish(self.waiter.until)
        bad = [name for name, result in results.items() if result["status"] != STEP_OK or result.get("commit_error")]
        reason = f"not ok: {', '.join(bad)}" if bad else "every part ok"
        return StepOutcome({}, {"status": STEP_FAILED if bad else STEP_OK, "reason": reason, "parts": results})
