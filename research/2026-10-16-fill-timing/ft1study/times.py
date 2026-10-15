"""E8's timing (PROTOCOL.md section 6): the card about 8 minutes after the decision, the fill at the first 15-minute
mark at or after card + R, and a mark after 15:25 moved to the next session at 09:15 + R. A price "at" a mark is the
close of the 15-minute candle that ends there, so the candle starts 15 minutes earlier."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

DECISION_15, DECISION_14 = time(15, 0), time(14, 0)
DECISIONS = (DECISION_15, DECISION_14)
REACTIONS = (5, 30, 60)  # minutes
CARD_DELAY = timedelta(minutes=8)
STEP = timedelta(minutes=15)
LAST_SAME_DAY_MARK = time(15, 25)
SESSION_OPEN = time(9, 15)


@dataclass(frozen=True, order=True)
class Moment:
    day: date
    at: time

    @property
    def naive(self) -> datetime:
        return datetime.combine(self.day, self.at)

    @property
    def candle_start(self) -> datetime:
        """The start of the 15-minute candle whose close is the price at this moment (naive, IST)."""
        return self.naive - STEP


def first_mark(target: datetime) -> datetime:
    """The first 15-minute mark (:00, :15, :30, :45) at or after `target`."""
    floor = target.replace(minute=target.minute - target.minute % 15, second=0, microsecond=0)
    return floor if floor == target else floor + STEP


def fill_moment(decision: Moment, reaction: int, next_session: Callable[[date], date]) -> Moment:
    mark = first_mark(decision.naive + CARD_DELAY + timedelta(minutes=reaction))
    if mark.time() > LAST_SAME_DAY_MARK:
        mark = first_mark(datetime.combine(next_session(decision.day), SESSION_OPEN) + timedelta(minutes=reaction))
    return Moment(mark.date(), mark.time())


def nights(decision: Moment, fill: Moment) -> int:
    return (fill.day - decision.day).days


def is_e4_snapshot(fill: Moment, decision: Moment) -> bool:
    """E4's 15:15 execution snapshot: the same time as a same-day 15:15 fill."""
    return fill.day == decision.day and fill.at == time(15, 15)
