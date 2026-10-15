"""The cue value an NSE session may use (story A17): the one known before 09:15 IST on that India date.

Rule: the latest row whose value date is **before** the India date. No cue's value of date t is known before
09:15 IST on t+1: the Treasury yield is published by about 04:30 IST on t+1 (US Eastern evening of t; a US close at
16:00 ET is 01:30 IST in US summer time, 02:30 IST in winter), the USD/INR reference rate at 13:00-13:30 IST on t
itself (after that day's open), Brent only at EIA's weekly release. So no same-date value is ever used, and a US
holiday simply has no row: for India date d the US value is the last US business date before d (a Tuesday after a US
Monday holiday gets Friday's).

With `live_only` the row must also have been first seen before 09:15 IST on d: the honest answer for a live decision.
Without it the rule-based answer is given for research on back-filled history, where the publication time is assumed,
not observed (and for Brent it is wrong by up to a week: EIA publishes weekly).
"""

from __future__ import annotations

from datetime import date, datetime

from ..models import IST
from .table import NSE_OPEN


def value_for(rows: list[dict[str, str]], india_day: date, live_only: bool) -> dict[str, str] | None:
    """The row a session on `india_day` may use, or None when there is none."""
    cutoff = datetime.combine(india_day, NSE_OPEN, tzinfo=IST)
    usable = [
        r
        for r in rows
        if date.fromisoformat(r["value_date"]) < india_day
        and (not live_only or datetime.fromisoformat(r["first_seen_at"]) < cutoff)
    ]
    return max(usable, key=lambda r: r["value_date"], default=None)
