"""How old a margin row may be (story C2, changed by C5): one strategy per profile.

The Manual paper account keeps C2's rule of 13 Oct 2026, a row at most `max_age_days` calendar days old. The books
follow design 6.1a (story C5): margin data older than one session means no new entry, so a row is fresh only when it
is dated on or after the session `sessions` sessions before the decision day (one session: the previous session's row,
or the day's own). A weekend or holiday therefore never ages a row, and a missed session's row always does.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from ..research_data.calendar import SessionCalendar


class MarginAge(ABC):
    @abstractmethod
    def fresh(self, as_of: date, day: date) -> bool:
        """Whether a margin row dated `as_of` may be used on `day` (as_of is on or before day)."""

    @abstractmethod
    def limit(self) -> str:
        """The rule in words, for the refusal reason."""


class DaysOld(MarginAge):
    def __init__(self, max_days: int):
        self.max_days = max_days

    def fresh(self, as_of: date, day: date) -> bool:
        return (day - as_of).days <= self.max_days

    def limit(self) -> str:
        return f"older than {self.max_days} days"


class SessionsOld(MarginAge):
    def __init__(self, calendar: SessionCalendar, sessions: int):
        self.calendar, self.sessions = calendar, sessions

    def oldest(self, day: date) -> date:
        """The oldest usable row date: the session `sessions` sessions before `day`."""
        for _ in range(self.sessions):
            day = self.calendar.previous_session(day)
        return day

    def fresh(self, as_of: date, day: date) -> bool:
        return as_of >= self.oldest(day)

    def limit(self) -> str:
        return f"older than {self.sessions} session(s)"
