"""Story O11: O1's steps for the replay. Each O1 command step runs `python -m fno ...` as a child process, which could
not see the replay's seams, so each command's own function is called in-process behind O1's `DayStep`, with O1's
outcome rules: a printed line is ok, a capture that wrote nothing is refused (the command prints "nothing written:"
and exits 0), and any raise is a failure. O1's real `Alerted` records each refusal or failure and alerts it once, and
O1's real `ReviewsStep` runs E6's scorecards."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from fno.constants import PLAYBOOK_FOLDER, REVIEWS_STEP, STEP_OK, STEP_REFUSED
from fno.daily.reviews import ReviewsStep, ScorecardReview
from fno.daily.steps import NOTHING_WRITTEN, Alerted
from fno.desk.daily_ports import DayStep
from fno.desk.daily_steps import StepOutcome
from fno.forecast_v4_rules.capture import CaptureRefused


class InProcessStep(DayStep):
    def __init__(self, command: Callable[[date], list[str]]):
        self.command = command

    def run(self, day: date) -> StepOutcome:
        try:
            lines = self.command(day)
        except CaptureRefused as refused:
            return StepOutcome({}, {"status": STEP_REFUSED, "reason": f"{NOTHING_WRITTEN} {refused}"})
        return StepOutcome({}, {"status": STEP_OK, "reason": lines[-1], "lines": lines})


def day_steps(commands: dict[str, Callable[[date], list[str]]], scorecards, snapshots, root, alerts) -> dict:
    """O1's steps by name, as `fno/daily/wiring.py` builds them (each command live: the replay is the live day)."""
    steps = {name: Alerted(name, InProcessStep(command), alerts) for name, command in commands.items()}
    reviews = ReviewsStep(
        (ScorecardReview(scorecards),), snapshots, root, lambda pathspecs: [], (f"{PLAYBOOK_FOLDER}/",)
    )
    return steps | {REVIEWS_STEP: Alerted(REVIEWS_STEP, reviews, alerts)}
