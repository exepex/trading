"""The quote parts as the daily run's steps (story O1): `quotes` starts them and goes on; `quotes_done`, after the
desk's exits, waits for those still running and records each part's result line and commit. `ServicingWaiter` is
the desk's waiter that commits a part as soon as it ends, while the desk waits for its next time."""

from __future__ import annotations

import time as clock_time
from collections.abc import Callable
from datetime import date, datetime, time

from ..constants import STEP_FAILED, STEP_NOT_LIVE, STEP_OK
from ..desk.daily_ports import DayStep, Waiter
from ..desk.daily_steps import StepOutcome
from ..models import IST
from .quote_parts import QuotePart, QuoteParts

POLL_SECONDS = 5.0


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


def start_time(part: QuotePart, results: dict[str, dict]) -> str:
    if results.get(part.name, {}).get("status") == STEP_NOT_LIVE:
        return "not live"
    if part.starts_after:
        return f"after {part.starts_after}"
    return f"from {part.not_before:%H:%M}" if part.not_before else "at the run's start"


class StartQuoteParts(DayStep):
    def __init__(self, parts: QuoteParts):
        self.parts = parts

    def run(self, day: date) -> StepOutcome:
        """The reason names when each part starts, "nifty, nse from 14:38; indices after nifty" (judge 178 add. 19)."""
        self.parts.start(day)
        starts: dict[str, list[str]] = {}
        for part in self.parts.parts:
            starts.setdefault(start_time(part, self.parts.results), []).append(part.name)
        reason = "; ".join(f"{', '.join(names)} {when}" for when, names in starts.items())
        return StepOutcome({"parts": [p.name for p in self.parts.parts]}, {"status": STEP_OK, "reason": reason})


class FinishQuoteParts(DayStep):
    def __init__(self, parts: QuoteParts, waiter: Waiter):
        self.parts, self.waiter = parts, waiter

    def run(self, day: date) -> StepOutcome:
        """The parts are always open here: started by this run's `quotes`, or resumed by a rerun (F1)."""
        results = self.parts.finish(self.waiter.until)
        fine = (STEP_OK, STEP_NOT_LIVE)  # a part not live yet (G10's `v4`) is no problem of the day
        bad = [name for name, result in results.items() if result["status"] not in fine or result.get("commit_error")]
        reason = f"not ok: {', '.join(bad)}" if bad else "every part ok"
        return StepOutcome({}, {"status": STEP_FAILED if bad else STEP_OK, "reason": reason, "parts": results})


class AfterPart(DayStep):
    """Runs its step once the quote part `name` has ended and its commit was made or tried, at most at `by` IST: a part
    still running then is stopped (G10's `v4_release` after the `v4` capture, by 14:45)."""

    def __init__(self, step: DayStep, parts: QuoteParts, name: str, by: time, waiter: Waiter):
        self.step, self.parts, self.name, self.by, self.waiter = step, parts, name, by, waiter

    def run(self, day: date) -> StepOutcome:
        self.parts.await_part(self.name, datetime.combine(day, self.by, IST), self.waiter.until)
        return self.step.run(day)
