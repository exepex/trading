"""How near the replay clock's now a recorded answer is served (story REH1, REH1g's gap G4).

- A scheduled read (A4h's closes, A16b's candles) is served the day's answer saved from `EARLIER` before now to
  `NEAREST` after it (`is_near`): the day saved its answer seconds to minutes after it asked.
- A paced read (A17e's cues, A22's pre-open parts, read every 30 s or one index after another) is served the day's copy
  nearest to now within `AROUND` either side, and never the same copy twice (`ServedOnce`): each of the day's reads
  had its own copy, so a retry is never handed the copy an earlier read already had.

An answer saved before now is no look-ahead: it existed then. One saved after now is served only once the replay clock
reaches its time (each source waits). `EARLIER` and `AROUND` are a minute because a rehearsal's reads drift a few
seconds from the day's (DRY2: KOSPI's copy at 08:50:34, read at 08:50:40, was missed at 5 s)."""

from __future__ import annotations

from collections.abc import Hashable, Iterable
from datetime import datetime, timedelta
from typing import TypeVar

EARLIER = timedelta(seconds=60)
NEAREST = timedelta(minutes=10)
AROUND = timedelta(seconds=60)

Copy = TypeVar("Copy", bound=Hashable)


def is_near(now: datetime, saved: datetime) -> bool:
    return now - EARLIER <= saved <= now + NEAREST


class ServedOnce:
    """The copies one process has served; a copy is marked served as soon as it is picked."""

    def __init__(self):
        self._served: set = set()

    def pick(self, now: datetime, copies: Iterable[tuple[datetime, Copy]]) -> tuple[datetime, Copy] | None:
        """The unserved copy saved nearest to now within `AROUND` (the earlier of two equally near), or None."""
        near = [(abs(saved - now), saved, copy) for saved, copy in copies
                if abs(saved - now) <= AROUND and copy not in self._served]  # fmt: skip
        if not near:
            return None
        _, saved, copy = min(near, key=lambda found: found[:2])
        self._served.add(copy)
        return saved, copy
