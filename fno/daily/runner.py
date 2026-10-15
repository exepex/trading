"""The day as one command (story O1): the daily run, then its one result line. After E3's commit-failure stop
(decision 44) the card does not run and nothing more of the desk is committed; the quote parts still running are
waited for and commit their own files (they are the recorder's data, not the desk's records)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from ..constants import STEP_FAILED, STEP_REFUSED
from ..desk.daily_ports import Waiter
from ..desk.daily_run import DailyRun, RunStopped
from .quote_parts import QuoteParts

DAY_DONE = "day done"
WITH_PROBLEMS = "day done with problems: {steps}"
NO_CARD = "; no card today"
PROBLEMS = (STEP_FAILED, STEP_REFUSED)


class DayRunner:
    def __init__(
        self, daily_run: DailyRun, parts: QuoteParts, waiter: Waiter, before: Callable[[], None] = lambda: None
    ):
        self.daily_run, self.parts, self.waiter, self.before = daily_run, parts, waiter, before

    def run(self, day: date) -> tuple[int, str]:
        """The exit code and the one line the command ends on. `before` runs first (the whole git history)."""
        self.before()
        try:
            log = self.daily_run.run(day)
        except RunStopped as stopped:
            if self.parts.started:
                self.parts.finish(self.waiter.until)
            return 1, f"{stopped}{NO_CARD}"
        problems = [name for name, step in log.steps.items() if step["result"].get("status") in PROBLEMS]
        return (1, WITH_PROBLEMS.format(steps=", ".join(problems))) if problems else (0, DAY_DONE)
