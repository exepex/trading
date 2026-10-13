"""The all-company announcement and board-meeting lists (story A12), one file per calendar day: archived by the existing
raw-data librarian (A9), which walks a calendar's days, so these lists get a calendar of every day (companies announce
on holidays and weekends too) and a content check.
"""

from __future__ import annotations

import json

from ..research_data.calendar import SessionCalendar

EVERY_DAY = "calendar day"


class EveryDayCalendar(SessionCalendar):
    """Every calendar day counts: the lists are published for days, not trading sessions."""

    def session_kind(self, day) -> str:
        return EVERY_DAY

    def calendar_sha256(self) -> str:
        return EVERY_DAY


def check_day_list(filename: str, data: bytes) -> None:
    """A day's list is a JSON array of objects (an empty array is a day without announcements); ValueError if not."""
    try:
        rows = json.loads(data)
    except ValueError as exc:
        raise ValueError(f"{filename}: not JSON: {exc}") from exc
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        raise ValueError(f"{filename}: not a list of announcements")
