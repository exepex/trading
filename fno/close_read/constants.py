"""A4h's fixed times, indices, Drive paths and printed lines. No line holds an index level (judge 440 SF1): O1 keeps
every printed line in the public `journal/runs/<date>.json`; the levels live in Drive only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

CLOSE_READ_FROM = time(15, 40)  # O1's `NotBefore` and a hand run's own gate: 10 minutes after NSE fixes the close
CLOSE_RECHECK_FROM = time(16, 0)  # the second read (judge 440 minor 1)
STAMP_FROM = time(15, 30)  # a list counts only when NSE stamped it today at or after the close
TRIES, TRY_GAP_SECONDS = 3, 60
TOLERANCE = 0.01  # points: "confirmed" within it (the official file has two decimals)
OVERDUE_SESSIONS = 2  # a day still unconfirmed at the second session after it alerts once
# A new day's confirm starts only this long after the run began (judge 447 add. 1): one day's archive retries can take
# about 5 minutes (5/15/45 s pauses and a 60 s timeout per try), so 240 + 300 s stays inside O1's 600 s command limit
# and a good read never ends "failed" (reasoning only, from the library's retry policy).
CONFIRM_STARTS_UNTIL_SECONDS = 240

ALL_INDICES_PATH = "/api/allIndices"  # the endpoint A4's market levels read (fno/quotes/market_levels.py)
STAMP_FORMAT = "%d-%b-%Y %H:%M"  # NSE's `timestamp`, e.g. "21-Oct-2026 15:30"
WRITER = "closeread"  # O9's writer name in each receipt
ROOT = "closes"  # under Drive's `data` area
DATA_AREA = "data"  # O9's area (fno/storage/data_wiring.py)


@dataclass(frozen=True)
class IndexName:
    listed: str  # its name in NSE's index list
    official: str  # its name in NSE's index-close file
    checked: bool  # False: the list's value is not the official close (INDIA VIX: 15.7 against 15.68 on 21 Oct)


INDICES = (
    IndexName("NIFTY 50", "Nifty 50", True),
    IndexName("NIFTY BANK", "Nifty Bank", True),
    IndexName("INDIA VIX", "India VIX", False),
)

READ, RECHECK = "first", "recheck"
NOT_A_SESSION = "not a trading day"
NOT_REGULAR = "nothing written: close not read: {kind} session (no close time in the calendar)"
TOO_EARLY = "too early: before {gate:%H:%M}"
ALREADY_READ = "close already read {day}"
ALREADY_RECHECKED = "close already rechecked {day}"
NOT_READ = "close not read: {reason}"
READ_LINE = "close read {day}{how}: {names} recorded, NSE stamp {stamp}, {path} sha256 {sha}"
AT_RECHECK = " at recheck (no first read to compare)"
RECHECK_LINE = "close recheck {day}: {results}, NSE stamp {stamp}, {path} sha256 {sha}"
CONFIRM_LINE = "close confirm {day}: {results}"
NOT_YET = "close confirm {day}: no official index-close file in Drive yet"
LEFT_FOR_NEXT_RUN = "close confirm: {count} earlier day(s) left for the next run (time budget)"
OVERDUE = "close confirm {day}: still not confirmed on {today} (no official index-close file); one alert"
DIFFERS_ALERT = "Omenix F&O close read: {day}'s provisional close differs from NSE's official file: {results}"
OVERDUE_ALERT = "Omenix F&O close read: {day}'s provisional close is still unconfirmed on {today}: no official file"
