"""The practice clock (story MS-SIM-d2): a session's decisions and fills happen at 15:31, after the close (15:30) the
practice snapshot is stamped with, so no fill precedes the data it rests on. Fixed per session, as a replay's is."""

from datetime import date, datetime, time

from ....models import IST
from ...contracts.clock import FixedClock

PRACTICE_TIME = time(15, 31)
PRACTICE_CLOCK_LABEL = "practice clock 15:31 (closing prices)"


def practice_clock(session: date) -> FixedClock:
    return FixedClock(datetime.combine(session, PRACTICE_TIME, tzinfo=IST))
