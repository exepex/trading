"""Decision days and their expiry (PROTOCOL.md sections 4 and 5): every A7 regular session of the window whose next
session is also regular, entering the nearest monthly expiry more than 7 sessions away. Every day left out is counted
by its reason."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta

from fno.research_data.calendar import SessionCalendar

from .contracts import MonthlyContracts

REGULAR = "regular"
MIN_SESSIONS_TO_EXPIRY = 7  # an entry needs more than this many sessions to expiry
NOT_REGULAR = "decision day is a special or muhurat session"
NEXT_NOT_REGULAR = "next session is special or muhurat"
NO_EXPIRY = "no monthly expiry more than 7 sessions away"


@dataclass(frozen=True)
class DecisionDay:
    day: date
    next_session: date
    expiry: date
    sessions_to_expiry: int


class Schedule:
    def __init__(self, calendar: SessionCalendar, contracts: MonthlyContracts):
        self.calendar, self.contracts = calendar, contracts

    def sessions_after(self, day: date, expiry: date) -> int:
        """Sessions of any kind after `day` up to and including `expiry`."""
        return len(self.calendar.sessions(day + timedelta(days=1), expiry))

    def decision_days(self, first: date, last: date) -> tuple[list[DecisionDay], Counter]:
        kept, left_out = [], Counter()
        for day in self.calendar.sessions(first, last):
            reason, found = self._judge(day)
            if reason:
                left_out[reason] += 1
            else:
                kept.append(found)
        return kept, left_out

    def _judge(self, day: date) -> tuple[str | None, DecisionDay | None]:
        if self.calendar.session_kind(day) != REGULAR:
            return NOT_REGULAR, None
        following = self.calendar.next_session(day)
        if self.calendar.session_kind(following) != REGULAR:
            return NEXT_NOT_REGULAR, None
        expiry = self.contracts.nearest(day, self.sessions_after, MIN_SESSIONS_TO_EXPIRY)
        if expiry is None:
            return NO_EXPIRY, None
        return None, DecisionDay(day, following, expiry, self.sessions_after(day, expiry))
