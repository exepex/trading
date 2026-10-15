"""The alert after two bad snapshots in a row (story A16): a SYSTEM alert (design 6.5), first line saying what to do,
one per streak of bad marks and at most one an hour. Its outcome line is kept in the ledger row that raised it."""

from __future__ import annotations

from datetime import datetime, timedelta

from .document import parse_time
from .status import GOOD

STREAK_LENGTH = 2
ALERT_GAP = timedelta(hours=1)
STREAK_ALERT = (
    "Action: check the 15-minute recorder (is its routine running, does Groww sign in?). SYSTEM, story A16: "
    "{count} bad snapshots in a row on {day}: {marks}. Gaps stay gaps; this session's realised variance will be void."
)


def streak_alert_text(rows: list[dict], now: datetime) -> str:
    """The alert to send now for the ledger's rows in mark order (the newest last), or empty when none is due."""
    streak = _trailing_bad(rows)
    if len(streak) < STREAK_LENGTH or any(row["alert"] for row in streak):
        return ""
    recent = [r for r in rows if r["alert"] and now - parse_time(r["first_seen_at"]) < ALERT_GAP]
    if recent:
        return ""
    marks = ", ".join(f"{r['mark_ist']} {r['status']} ({r['failures']})" for r in streak)
    return STREAK_ALERT.format(count=len(streak), day=rows[-1]["session"], marks=marks)


def _trailing_bad(rows: list[dict]) -> list[dict]:
    streak: list[dict] = []
    for row in reversed(rows):
        if row["status"] == GOOD:
            break
        streak.insert(0, row)
    return streak
