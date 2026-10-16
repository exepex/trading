"""When a feed is stale (story A19, scope 8; judge 352 SF5): no new item or version for longer than its limits,
counted two ways at once. Session hours are the time inside 09:00-18:00 IST on NSE session days (A7's calendar), so
nights, weekends and holidays add none and Monday 09:15 is never stale from Sunday's silence; all hours count every
hour. A day outside the calendar's range counts as a session day on a weekday (the stricter reading: a missing
calendar year must not switch the check off; O8 already warns of the calendar's end)."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from ..constants import SESSION_REGULAR, SESSION_SPECIAL
from ..models import IST
from ..research_data.calendar import CalendarError, SessionCalendar
from .settings import Feed

SESSION_START, SESSION_END = time(9, 0), time(18, 0)
SATURDAY = 5
HOUR = timedelta(hours=1)
DAY_SESSIONS = (SESSION_REGULAR, SESSION_SPECIAL)


class StaleRule:
    def __init__(self, calendar: SessionCalendar):
        self.calendar = calendar

    def is_stale(self, feed: Feed, last_new: datetime, now: datetime) -> bool:
        if now - last_new > feed.stale_any_hours * HOUR:
            return True
        return self.session_time(last_new, now) > feed.stale_session_hours * HOUR

    def session_time(self, start: datetime, end: datetime) -> timedelta:
        total, day = timedelta(0), start.astimezone(IST).date()
        while day <= end.astimezone(IST).date():
            if self.is_trading_day(day):
                opens = datetime.combine(day, SESSION_START, tzinfo=IST)
                closes = datetime.combine(day, SESSION_END, tzinfo=IST)
                total += max(timedelta(0), min(end, closes) - max(start, opens))
            day += timedelta(days=1)
        return total

    def is_trading_day(self, day) -> bool:
        try:
            return self.calendar.session_kind(day) in DAY_SESSIONS  # a muhurat evening is not a trading day's hours
        except CalendarError:
            return day.weekday() < SATURDAY
