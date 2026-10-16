"""The rates as they were known at a moment (story A21): each rate's latest value first seen at or before the cutoff,
never a later one. G13 and S6's freeze read rates through this, never through the newest row."""

from __future__ import annotations

from datetime import datetime

from .rows import RateRow


class RatesAsOf:
    def __init__(self, rows: list[RateRow]):
        self.rows = rows

    def value(self, rate: str, cutoff: datetime) -> RateRow | None:
        known = [row for row in self.rows if row.rate == rate and row.seen_at <= cutoff]
        return max(known, key=lambda row: (row.value_date, row.seen_at)) if known else None
