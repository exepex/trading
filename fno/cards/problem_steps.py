"""The card's line naming the desk steps that failed or were refused today (story T1d): read from the committed run
log through T2's reader, with O1's own rule (`problem_steps`), never by matching text. No line when none."""

from __future__ import annotations

from datetime import date

from ..desk.run_log import problem_steps
from .rule_checks import RunLogReader, UnreadableRecord

LINE = "Steps with problems today: {steps}"  # the orchestrator's wording, 24 Oct 2026


class ProblemSteps:
    def __init__(self, runs: RunLogReader):
        self.runs = runs

    def line(self, day: date) -> str | None:
        try:
            steps, _ = self.runs.steps(day)
        except UnreadableRecord:  # T2's rule checks already name the unreadable run log on the card
            return None
        found = problem_steps(steps or {})
        return LINE.format(steps=", ".join(f"{name} ({status})" for name, status in found)) if found else None
