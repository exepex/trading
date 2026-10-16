"""Reading the captured news back (story A19, scope 10, and the stale limits' evidence, scope 8). Point in time is
enforced here, not left to callers: `known_by(T)` returns only items first seen at or before T, each in its latest
version first seen by then. `quiet_spells` measures each feed's longest gap between new items by day type, the
evidence the stale limits are reset from after 10 sessions."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta

from ..models import IST
from .names import ITEM_LINE
from .stale import SESSION_END, SESSION_START, StaleRule

SESSION_HOURS, SESSION_NIGHT, CLOSED_DAY = "session hours", "session night", "closed day"


def known_by(lines: list[dict], until: datetime, since: datetime | None = None) -> list[dict]:
    """Each item's latest version first seen at or before `until` (and its first sighting after `since`)."""
    latest: dict[str, dict] = {}
    first: dict[str, datetime] = {}
    for line in lines:
        if line["line"] != ITEM_LINE:
            continue
        seen = datetime.fromisoformat(line["first_seen_at"])
        if seen > until:
            continue
        key = line["item_id"]
        first[key] = min(first.get(key, seen), seen)
        if key not in latest or seen >= datetime.fromisoformat(latest[key]["first_seen_at"]):
            latest[key] = line
    chosen = [line for key, line in latest.items() if since is None or first[key] >= since]
    return sorted(chosen, key=lambda line: line["first_seen_at"])


def quiet_spells(lines: list[dict], rule: StaleRule) -> dict[str, dict[str, timedelta]]:
    """Feed -> day type -> the longest gap between two consecutive new items or versions; a gap is filed under the
    day type of its start."""
    seen: dict[str, list[datetime]] = defaultdict(list)
    for line in lines:
        if line["line"] == ITEM_LINE:
            seen[line["feed"]].append(datetime.fromisoformat(line["first_seen_at"]))
    spells: dict[str, dict[str, timedelta]] = {}
    for feed, moments in seen.items():
        moments.sort()
        longest: dict[str, timedelta] = {}
        for start, end in zip(moments, moments[1:], strict=False):
            kind = day_type(start, rule)
            longest[kind] = max(longest.get(kind, timedelta(0)), end - start)
        spells[feed] = longest
    return spells


def day_type(moment: datetime, rule: StaleRule) -> str:
    local = moment.astimezone(IST)
    if not rule.is_trading_day(local.date()):
        return CLOSED_DAY
    return SESSION_HOURS if _within(local.time(), SESSION_START, SESSION_END) else SESSION_NIGHT


def _within(clock: time, start: time, end: time) -> bool:
    return start <= clock < end
