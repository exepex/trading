"""NSE trading days and the phases of a session, in IST."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from ..constants import SessionPhase
from ..models import IST

WEEKEND_START = 5  # Saturday


def parse_clock(text: str) -> time:
    hour, minute = text.split(":")
    return time(int(hour), int(minute))


@dataclass(frozen=True)
class SessionTimes:
    pre_open: time = time(9, 0)
    market_open: time = time(9, 15)
    opening_range_minutes: int = 15
    no_new_entries_after: time = time(14, 45)
    square_off: time = time(15, 15)
    market_close: time = time(15, 30)

    @classmethod
    def from_config(cls, holding_cfg: dict, opening_range_minutes: int = 15) -> SessionTimes:
        return cls(
            opening_range_minutes=opening_range_minutes,
            no_new_entries_after=parse_clock(holding_cfg.get("no_new_entries_after", "14:45")),
            square_off=parse_clock(holding_cfg.get("intraday_square_off", "15:15")),
        )


class MarketClock:
    def __init__(self, times: SessionTimes, holidays: set[date] | None = None):
        self.times = times
        self.holidays = holidays or set()

    def is_trading_day(self, day: date) -> bool:
        return day.weekday() < WEEKEND_START and day not in self.holidays

    def phase(self, now: datetime) -> SessionPhase:
        now = now.astimezone(IST)
        if not self.is_trading_day(now.date()):
            return SessionPhase.CLOSED
        t, s = now.time(), self.times
        opening_range_end = (
            datetime.combine(now.date(), s.market_open) + timedelta(minutes=s.opening_range_minutes)
        ).time()
        if t < s.pre_open or t >= s.market_close:
            return SessionPhase.CLOSED
        if t < s.market_open:
            return SessionPhase.PRE_OPEN
        if t < opening_range_end:
            return SessionPhase.OPENING_RANGE
        if t < s.no_new_entries_after:
            return SessionPhase.TRADING
        if t < s.square_off:
            return SessionPhase.NO_NEW_ENTRIES
        return SessionPhase.SQUARE_OFF

    def trading_days_held(self, opened: date, today: date) -> int:
        """1 on the entry day, 2 on the next trading day, and so on."""
        days, day = 0, opened
        while day <= today:
            days += self.is_trading_day(day)
            day += timedelta(days=1)
        return max(days, 1)

    def previous_session_close(self, now: datetime) -> datetime:
        """Close of the last full session before today: news after it is 'new' for today's trading."""
        day = self.previous_trading_day(now.astimezone(IST).date())
        return datetime.combine(day, self.times.market_close, tzinfo=IST)

    def previous_trading_day(self, day: date) -> date:
        day -= timedelta(days=1)
        while not self.is_trading_day(day):
            day -= timedelta(days=1)
        return day
