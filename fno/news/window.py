"""The polling window in IST (story A19, owner 16 Oct: 07:00-23:00, `news.active_window`): whether a moment is
inside it, when it next opens or closes, and how much of a stretch of time lies inside it (the coverage gap counts
only that part, so the closed night is never a gap)."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from ..models import IST
from .settings import Window

ONE_DAY = timedelta(days=1)


class PollingWindow:
    def __init__(self, window: Window):
        self.window = window

    def is_open(self, moment: datetime) -> bool:
        if self.window.all_day:
            return True
        clock = moment.astimezone(IST).time()
        start, end = self.window.start, self.window.end
        return start <= clock < end if start < end else clock >= start or clock < end

    def next_open(self, moment: datetime) -> datetime:
        """`moment` itself when open, else the next opening."""
        if self.is_open(moment):
            return moment
        opening = _at(moment, self.window.start)
        return opening if opening > moment else opening + ONE_DAY

    def next_close(self, moment: datetime) -> datetime | None:
        """The next closing after `moment` (None for an all-day window)."""
        if self.window.all_day:
            return None
        closing = _at(moment, self.window.end)
        return closing if closing > moment else closing + ONE_DAY

    def time_open(self, start: datetime, end: datetime) -> timedelta:
        """How much of [start, end) lies inside the window."""
        total, moment = timedelta(0), start
        while moment < end:
            if self.is_open(moment):
                stop = min(end, self.next_close(moment) or end)
                total += stop - moment
            else:
                stop = min(end, self.next_open(moment))
            moment = stop
        return total


def _at(moment: datetime, clock: time) -> datetime:
    local = moment.astimezone(IST)
    return datetime.combine(local.date(), clock, tzinfo=IST)
