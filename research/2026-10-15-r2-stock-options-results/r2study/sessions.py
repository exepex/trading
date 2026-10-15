"""NSE sessions and the protocol's timing rules (PROTOCOL.md section 4, amendment 1 section D5)."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from datetime import date, datetime, time

from .rules import MARKET_CLOSE, MARKET_OPEN, MIN_SESSIONS_AFTER_R

OPEN, CLOSE = time(*MARKET_OPEN), time(*MARKET_CLOSE)


class Sessions:
    """The sorted list of NSE sessions with an F&O file (`days`); `later` adds the calendar's sessions after the last
    file, used only to count sessions up to an expiry (amendment 1 D5)."""

    def __init__(self, days, later=()):
        self.days = sorted(set(days))
        self._position = {day: i for i, day in enumerate(self.days)}
        self._counted = sorted(set(self.days) | {d for d in later if not self.days or d > self.days[-1]})

    def __contains__(self, day: date) -> bool:
        return day in self._position

    @property
    def last(self) -> date:
        return self.days[-1]

    def before(self, day: date) -> date | None:
        """The last session strictly before a day."""
        i = bisect_left(self.days, day)
        return self.days[i - 1] if i > 0 else None

    def after(self, day: date) -> date | None:
        """The first session strictly after a day."""
        i = bisect_right(self.days, day)
        return self.days[i] if i < len(self.days) else None

    def on_or_after(self, day: date) -> date | None:
        i = bisect_left(self.days, day)
        return self.days[i] if i < len(self.days) else None

    def window_ending(self, day: date, count: int) -> list[date]:
        """The `count` sessions ending at a session (fewer at the start of the list)."""
        i = self._position[day]
        return self.days[max(0, i - count + 1) : i + 1]

    def between(self, start: date, end: date) -> int:
        """Sessions strictly after `start` up to and including `end`."""
        return bisect_right(self._counted, end) - bisect_right(self._counted, start)

    def ahead(self, day: date, count: int) -> list[date]:
        """The next `count` sessions strictly after a day."""
        i = bisect_right(self.days, day)
        return self.days[i : i + count]


def reaction_session(sessions: Sessions, results_day: date, filed_at: datetime | None) -> date | None:
    """R: the session holding the filing if filed in market hours; else the first session after the filing. With no
    filing time, the first session after D (the conservative after-hours case)."""
    if filed_at is None:
        return sessions.after(results_day)
    day, moment = filed_at.date(), filed_at.time().replace(tzinfo=None)
    if day in sessions and OPEN <= moment <= CLOSE:
        return day
    if moment < OPEN:
        return sessions.on_or_after(day)
    return sessions.after(day)


def filed_before_entry_close(filed_at: datetime | None, entry: date) -> bool:
    """A filing at or before the entry session's close: the decision would not have been made blind (excluded)."""
    return filed_at is not None and (filed_at.date(), filed_at.time().replace(tzinfo=None)) <= (entry, CLOSE)


def choose_expiry(sessions: Sessions, listed: list[date], reaction: date) -> tuple[date | None, bool]:
    """The nearest listed expiry at least MIN_SESSIONS_AFTER_R sessions after R, and whether that pushed the event past
    the nearest expiry on or after R (a "push to the second month")."""
    upcoming = sorted(e for e in listed if e >= reaction)
    for expiry in upcoming:
        if sessions.between(reaction, expiry) >= MIN_SESSIONS_AFTER_R:
            return expiry, expiry != upcoming[0]
    return None, bool(upcoming)
