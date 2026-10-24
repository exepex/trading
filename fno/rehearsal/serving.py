"""How near the replay clock's now a recorded answer is served (story REH1): the answer the day saved from `EARLIER`
before now to `NEAREST` after it, once the clock reaches its time. One rule for every recorded source (REH1g).

An answer saved before now is no look-ahead: it existed then. `EARLIER` is a minute because a rehearsal's paced
reads drift a few seconds from the day's (DRY2: KOSPI's copy at 08:50:34, read at 08:50:40, was missed at 5 s)."""

from __future__ import annotations

from datetime import datetime, timedelta

EARLIER = timedelta(seconds=60)
NEAREST = timedelta(minutes=10)


def is_near(now: datetime, saved: datetime) -> bool:
    return now - EARLIER <= saved <= now + NEAREST
