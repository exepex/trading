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


def usdinr_rows(rbi: list[dict[str, str]], fbil: list[dict[str, str]]) -> list[dict[str, str]]:
    """One USD/INR reference rate: RBI's rows, and FBIL's for the dates RBI lacks (RBI's hole, 24 Jul 2018 - 12 Apr
    2022, after FBIL took the benchmark over). A17's README: the two are equal on all 1,086 dates both publish
    (protocol deviation of 22 Oct, section 14). Read under RBI's rule (13:30 IST, 5 days)."""
    held = {r["value_date"] for r in rbi}
    return sorted([*rbi, *(r for r in fbil if r["value_date"] not in held)], key=lambda r: r["value_date"])


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
