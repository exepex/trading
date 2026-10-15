"""Whether the data routines' sessions are captured (judge 104 addendum 1). On the measured basis their minutes sit in
the denominator, so a missed run makes the books' share look higher than it is: the measured level is not known until
every expected run is recorded. Each data routine named in `budget.data_routines` runs once on every NSE session day
(the 3 pm quote recorder today); its run is recorded by the routine's own timing record (`record-usage --self-timed
--purpose data_routines --role <name>`). Adding that record to a routine's prompt is the owner's step."""

from __future__ import annotations

from datetime import date, timedelta

from ..constants import PURPOSE_DATA_ROUTINES
from ..research_data.calendar import CalendarError, SessionCalendar

MISSING = "data routines not fully captured: {n} of {expected} expected run(s) recorded ({names})"
NO_CALENDAR = "data routines not checked: {error}"


def routine_gap(routines: list[str], usage: list[dict], month: str, before: date, sessions: SessionCalendar) -> str:
    """Why the month's data-routine runs are not all captured, or empty when they are (or none is named)."""
    if not routines:
        return ""
    first = date.fromisoformat(month + "-01")
    next_month = date(first.year + first.month // 12, first.month % 12 + 1, 1)
    last = min(before, next_month) - timedelta(days=1)
    try:
        days = sessions.sessions(first, last) if last >= first else []
    except CalendarError as error:
        return NO_CALENDAR.format(error=error)
    seen = {(r["role_or_bundle"], r["date"]) for r in usage if r["purpose"] == PURPOSE_DATA_ROUTINES}
    expected = [(name, day.isoformat()) for name in routines for day in days]
    found = sum(1 for run in expected if run in seen)
    return "" if found == len(expected) else MISSING.format(n=found, expected=len(expected), names=", ".join(routines))
