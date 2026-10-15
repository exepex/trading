"""The cue value an NSE session may use at a cutoff on its India date (story A17).

Two cutoffs (design 2.1; orchestrator, 15 Oct 2026), chosen explicitly:
- `OPEN` (09:15 IST): what was known before the open, for overnight gaps;
- `DECISION` (15:00 IST): what was known at the desk's decision time; it adds the same day's USD/INR reference rate,
  published at about 13:00-13:30 IST.

Rule: a value is usable when its source says it was final and published before the cutoff (`available_at`: the US
close at 16:00 US Eastern, so 01:30 IST in US summer time and 02:30 IST in winter on the next day; the Treasury yield
by 18:00 US Eastern, an assumption; the reference rate at 13:30 IST; Brent within 8 days of its date, an assumption).
A US holiday simply has no row, so a Tuesday after a US Monday holiday gets Friday's close.

With `live_only` the row must also have been first seen by this tool before the cutoff (`first_seen_at`): the honest
answer for a live decision. Without it, the rule's answer is given for research on back-filled history, where the
publication time is the source's stated rule, not an observation.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, time

from ..models import IST

OPEN, DECISION = time(9, 15), time(15, 0)


def value_for(
    rows: list[dict[str, str]],
    india_day: date,
    cutoff: time,
    live_only: bool,
    available_at: Callable[[date], datetime],
) -> dict[str, str] | None:
    """The newest row usable on `india_day` at `cutoff` (IST), or None when there is none."""
    moment = datetime.combine(india_day, cutoff, tzinfo=IST)
    usable = [
        r
        for r in rows
        if available_at(date.fromisoformat(r["value_date"])) < moment
        and (not live_only or datetime.fromisoformat(r["first_seen_at"]) < moment)
    ]
    return max(usable, key=lambda r: r["value_date"], default=None)
