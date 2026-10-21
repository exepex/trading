"""A calendar with no permitted source yet (story A20c, open question 1): US CPI and payrolls. BLS refuses this
container and GitHub's runners (403, probe run 38900266338, 16 Oct 2026); the owner decides on a free FRED key.
Every run reports it as a failure, so the gap is never silent."""

from __future__ import annotations

from datetime import date

from .model import Calendar, CalendarFailed

NOT_CONFIGURED = "{kinds}: no source configured: set the GitHub secret FNO_FRED_API_KEY (BLS refuses GitHub's runners)"


class UnconfiguredCalendar:
    def __init__(self, source: str, kinds: tuple[str, ...]):
        self.source, self.kinds = source, kinds

    def fetch(self, today: date) -> Calendar:
        raise CalendarFailed(NOT_CONFIGURED.format(kinds=", ".join(self.kinds)))
