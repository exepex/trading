"""The routines the watcher expects, with their IST start times (story O13). Each name is the `--routine` its prompt
or CLAUDE.md section passes to `routine-log`. Keep this list in step with the scheduled tasks: a task added without a
row here is logged but never missed; a row without a task is reported missing every day."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time

TRADING_DAYS, FIRST_OF_MONTH = "trading days", "first of month"
GRACE_MINUTES = 15  # a run must log its begin within this long of its start time


@dataclass(frozen=True)
class RoutineSpec:
    name: str
    starts: tuple[time, ...]
    days: str  # TRADING_DAYS: NSE's calendar decides; FIRST_OF_MONTH: every 1st
    max_minutes: int  # by then `end.json` must be there, or the run counts as stuck or died

    def due_on(self, day: date, is_session: bool) -> bool:
        return day.day == 1 if self.days == FIRST_OF_MONTH else is_session


def _hourly(first: int, last: int, minute: int) -> tuple[time, ...]:
    return tuple(time(hour, minute) for hour in range(first, last + 1))


ROUTINES = (
    RoutineSpec("a16-backup", (time(8, 22),), TRADING_DAYS, 185),
    RoutineSpec("pre-open", (time(8, 36),), TRADING_DAYS, 45),
    RoutineSpec("morning-forecast", (time(8, 38),), TRADING_DAYS, 40),
    RoutineSpec("a16-recorder", _hourly(8, 14, 52), TRADING_DAYS, 160),
    RoutineSpec("daily-desk", (time(14, 5),), TRADING_DAYS, 150),
    RoutineSpec("participant-oi", (time(17, 11),), TRADING_DAYS, 400),
    RoutineSpec("evening-forecast", (time(19, 53),), TRADING_DAYS, 60),
    RoutineSpec("participant-oi-sweep", (time(7, 7),), FIRST_OF_MONTH, 60),
)
