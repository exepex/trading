"""A global cue's last-published move at a cutoff, by A17's own point-in-time rule (protocol section 3; judge 428
SF2): the newest row whose source says it was final and published before the cutoff (`value_for(live_only=False)`
with the source's `available_at`), refused when older than the source's `max_age_days`; its move is against the
row before it. Never a raw `value_date < d`."""

from __future__ import annotations

import math
from datetime import date, time

from fno.global_cues.as_of import value_for

DECISION_CUTOFF, OPEN_CUTOFF = time(15, 30), time(9, 15)
LEVEL_CUES = ("us10y",)  # a yield: its move is a difference in points; the others are log moves
DAY_BEFORE_CUES = ("usdinr_rbi",)  # RBI's rate of d-1 at the latest (section 3): read at 09:15, before d's 13:30 rate


def cutoff_for(cue: str, cutoff: time) -> time:
    return OPEN_CUTOFF if cue in DAY_BEFORE_CUES else cutoff


def cue_move(rows: list[dict[str, str]], source, india_day: date, cutoff: time) -> float | None:
    usable = [r for r in rows if date.fromisoformat(r["value_date"]) <= india_day]
    row = value_for(usable, india_day, cutoff, False, source.available_at)
    if row is None or (india_day - date.fromisoformat(row["value_date"])).days > source.max_age_days:
        return None
    before = [r for r in usable if r["value_date"] < row["value_date"]]
    if not before:
        return None
    prior = max(before, key=lambda r: r["value_date"])
    value, previous = float(row["value"]), float(prior["value"])
    return abs(value - previous) if source.cue in LEVEL_CUES else abs(math.log(value / previous))
