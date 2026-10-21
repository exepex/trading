"""What F2 and the owner read (story A21 part 2): the items known at a cutoff, by first-seen time only (never NSE's
own time), and the day's coverage of the window's 20 marks, so a gap shows as a gap."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from ..models import IST
from .constants import WINDOW_FIRST, WINDOW_LAST

NO_POLL = "no poll (no mark)"


def items_as_of(items: list[dict], cutoff: datetime) -> list[dict]:
    """Every item first seen at or before the cutoff; `exchdisstime` stays beside it, never in its place."""
    return [row for row in items if datetime.fromisoformat(row["first_seen_at"]) <= cutoff]


def window_marks(day: date) -> list[datetime]:
    first = datetime.combine(day, WINDOW_FIRST, IST)
    last = datetime.combine(day, WINDOW_LAST, IST)
    return [first + timedelta(minutes=15 * i) for i in range(int((last - first).total_seconds() // 900) + 1)]


def coverage(day: date, polls: list[dict]) -> list[tuple[str, str]]:
    """(mark, what happened) for each of the window's marks: `polled ok`, `polled failed (kind)` or `no poll`."""
    by_mark = {datetime.fromisoformat(p["mark"]).astimezone(IST).strftime("%H:%M"): p for p in polls}
    lines = []
    for mark in window_marks(day):
        poll = by_mark.get(f"{mark:%H:%M}")
        if poll is None:
            lines.append((f"{mark:%H:%M}", NO_POLL))
        else:
            kind = f" ({poll['kind']})" if poll["status"] != "ok" and poll["kind"] else ""
            lines.append((f"{mark:%H:%M}", f"polled {poll['status']}{kind}"))
    return lines
