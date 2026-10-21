"""Sealing (part A5): a live record counts only when its receipt reached `origin/main` by the issue's deadline, by
GitHub's own push time (O8's `Evidence.file_pushed_at`, GitHub's activity log), never a commit date. Push evidence
that is unavailable means `late`, never assumed sealed."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime

from ..models import IST
from ..price_distribution.horizons import nth_regular_session
from ..research_data.calendar import CalendarError, SessionCalendar
from .constants import DEADLINE

NO_EVIDENCE = "late: push time unknown ({why})"
PAST_DEADLINE = "late: pushed {pushed} after the deadline {deadline}"


@dataclass(frozen=True)
class Seal:
    sealed_at: datetime | None
    deadline: datetime | None
    late: bool
    reason: str | None = None


class SealCheck:
    def __init__(self, pushed_at: Callable[[str], datetime], calendar: SessionCalendar):
        """`pushed_at(repository path)`: GitHub's receipt time of the commit that first added the file; raises when
        unknown."""
        self.pushed_at, self.calendar = pushed_at, calendar

    def deadline(self, day: date) -> datetime | None:
        """09:15 IST of the next regular session (a 15:45 issue)."""
        try:
            return datetime.combine(nth_regular_session(self.calendar, day, 1), DEADLINE, IST)
        except CalendarError:
            return None

    def seal(self, receipt_path: str, day: date) -> Seal:
        deadline = self.deadline(day)
        try:
            pushed = self.pushed_at(receipt_path)
        except Exception as error:  # noqa: BLE001 - any evidence failure is "late", never "sealed"
            return Seal(None, deadline, True, NO_EVIDENCE.format(why=f"{type(error).__name__}: {error}"))
        if deadline is None or pushed > deadline:
            return Seal(pushed, deadline, True, PAST_DEADLINE.format(pushed=pushed, deadline=deadline))
        return Seal(pushed, deadline, False)
