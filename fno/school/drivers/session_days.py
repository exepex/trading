"""Trading-day counting for the cards' session rules (story MS-P1e). The NSE session calendar (story A7, through
`TradingDays`) answers; this module only counts."""

from datetime import date, timedelta
from typing import Protocol


class TradingCalendar(Protocol):
    def is_trading_day(self, day: date) -> bool: ...


def sessions_between(calendar: TradingCalendar, after: date, through: date) -> int:
    """Trading sessions in (after, through]: 1 on the day before an expiry for `through` = the expiry."""
    return sum(calendar.is_trading_day(after + timedelta(days=n)) for n in range(1, (through - after).days + 1))


def previous_session(calendar: TradingCalendar, day: date) -> date:
    day -= timedelta(days=1)
    while not calendar.is_trading_day(day):
        day -= timedelta(days=1)
    return day


def next_session(calendar: TradingCalendar, day: date) -> date:
    day += timedelta(days=1)
    while not calendar.is_trading_day(day):
        day += timedelta(days=1)
    return day
