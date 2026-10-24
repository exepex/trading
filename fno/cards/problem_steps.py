"""The card's warning about the desk steps that failed or were refused today (stories T1d and T1e): read from the
committed run log through T2's reader, with O1's own rule (`problem_steps`), never by matching text. A run log that
exists but cannot be read is a warning too, since the card then cannot say which steps worked. None when all is well."""

from __future__ import annotations

from datetime import date

from ..desk.run_log import problem_steps
from .rule_checks import RunLogReader, UnreadableRecord
from .sections import CardWarning

GLYPH = "⚠️ WARNING:"  # the word and the glyph, never colour alone (owner, 24 Oct 2026)
FAILED = CardWarning(
    f"{GLYPH} part of today's desk run did not work.",
    "Steps with problems today: {steps}. Their alerts in #fno-desk give the reasons.",  # T1d's list, the orchestrator's
)
UNREADABLE = CardWarning(
    f"{GLYPH} today's run log could not be read.", "This card cannot say which desk steps worked. See #fno-desk."
)


class ProblemSteps:
    def __init__(self, runs: RunLogReader):
        self.runs = runs

    def warning(self, day: date) -> CardWarning | None:
        try:
            steps, _ = self.runs.steps(day)
        except UnreadableRecord:  # T2's rule checks name the file; the warning puts the doubt in the headline
            return UNREADABLE
        found = problem_steps(steps or {})  # O1's one rule; the reader has already refused an odd shape
        if not found:
            return None
        listed = ", ".join(f"{name} ({status})" for name, status in found)  # the status only: reasons are in alerts
        return CardWarning(FAILED.headline, FAILED.detail.format(steps=listed))
