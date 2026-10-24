"""Every report in a rehearsal (story REH1c; the orchestrator's ruling for the owner, 24 Oct: "all type of data and
reports ... send to slack for review"): a step that is not live on the replayed day in real runs runs in the
rehearsal, and each of its posts says so in one more line. Chosen in the daily run's composition root; real runs and
`config.yaml` are untouched. E8's owner-timing fills are not a report (they change the desk's fills), so they keep
their real live date."""

from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import date

from ..constants import ENV_FNO_REHEARSAL_NOT_LIVE, OWNER_TIMING_STEP
from ..desk.daily_ports import DayStep
from ..desk.daily_steps import StepOutcome
from .mode import rehearsal

NOT_LIVE_UNSET = "not live in real runs yet (live_from unset)"
NOT_LIVE_UNTIL = "not live in real runs on {day} (live from {live_from})"
KEPT_REAL = (OWNER_TIMING_STEP,)


def rehearsed_live(live: dict[str, date | None], env: Mapping[str, str] = os.environ):
    """The live dates the run uses, and each step made live for the rehearsal with the line its posts carry."""
    mode = rehearsal(env)
    if mode is None:
        return live, {}
    notes = {name: (NOT_LIVE_UNSET if real is None else NOT_LIVE_UNTIL.format(day=mode.day, live_from=real))
             for name, real in live.items() if name not in KEPT_REAL and (real is None or mode.day < real)}  # fmt: skip
    return {**live, **dict.fromkeys(notes, mode.day)}, notes


def rehearsed_not_live(steps: dict[str, DayStep], notes: Mapping[str, str]) -> dict[str, DayStep]:
    return {name: NotLiveInRealRuns(step, notes[name]) if name in notes else step for name, step in steps.items()}


class NotLiveInRealRuns(DayStep):
    """Runs its step with the note in the environment, so every post of the step's process and its children carries
    it (the label decorators read it); the note is gone once the step ends."""

    def __init__(self, step: DayStep, note: str):
        self.step, self.note = step, note

    def run(self, day: date) -> StepOutcome:
        os.environ[ENV_FNO_REHEARSAL_NOT_LIVE] = self.note
        try:
            return self.step.run(day)
        finally:
            os.environ.pop(ENV_FNO_REHEARSAL_NOT_LIVE, None)
