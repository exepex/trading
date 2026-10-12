"""Measures when NSE first publishes a session's file, and sets the availability rule from that evidence (story A8).

The recorder checks the archive on a schedule and appends every check to a committed log (`day, checked_at, outcome,
sha256`); it never edits a row. A day counts as measured only when the log shows its file absent and later present,
so the release falls between two checks. The first `present` time is used: an upper bound on the real release, the
safe side for look-ahead. Until `MIN_MEASURED_DAYS` days are measured, the default next-session rule applies.
"""

from __future__ import annotations

import csv
import hashlib
import time as clock_time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

from ..constants import RELEASE_ABSENT, RELEASE_PRESENT, RELEASE_UNREACHABLE
from ..models import now_ist
from ..storage.raw_source import RawFileSource, RawSourceUnavailable
from .availability import AvailabilityRule, MeasuredReleaseRule, NextSessionRule, sessions_until_usable
from .calendar import SessionCalendar

LOG_FIELDS = ("day", "checked_at", "outcome", "sha256")
MIN_MEASURED_DAYS = 20


@dataclass(frozen=True)
class ReleaseCheck:
    day: date
    checked_at: datetime
    outcome: str  # RELEASE_PRESENT, RELEASE_ABSENT or RELEASE_UNREACHABLE (no answer: says nothing about the file)
    sha256: str = ""


class ReleaseLog:
    """The append-only CSV of checks."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def checks(self) -> list[ReleaseCheck]:
        if not self.path.is_file():
            return []
        rows = csv.DictReader(self.path.read_text(encoding="utf-8").splitlines())
        return [
            ReleaseCheck(
                date.fromisoformat(r["day"]), datetime.fromisoformat(r["checked_at"]), r["outcome"], r["sha256"]
            )
            for r in rows
        ]

    def append(self, check: ReleaseCheck) -> None:
        new = not self.path.is_file()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, lineterminator="\n")
            if new:
                writer.writerow(LOG_FIELDS)
            writer.writerow([check.day.isoformat(), check.checked_at.isoformat(), check.outcome, check.sha256])


def first_seen_times(checks: list[ReleaseCheck]) -> dict[date, datetime]:
    """Day -> the first time its file was seen, for days whose file was seen absent before it was seen."""
    seen = {}
    for day in sorted({c.day for c in checks}):
        ordered = sorted((c for c in checks if c.day == day), key=lambda c: c.checked_at)
        present = next((c for c in ordered if c.outcome == RELEASE_PRESENT), None)
        if present and any(c.outcome == RELEASE_ABSENT and c.checked_at < present.checked_at for c in ordered):
            seen[day] = present.checked_at
    return seen


def choose_availability_rule(
    checks: list[ReleaseCheck], calendar: SessionCalendar, decision_time: time
) -> AvailabilityRule:
    """The measured rule (the largest lag in sessions) once enough days are measured, else the next-session rule."""
    seen = first_seen_times(checks)
    if len(seen) < MIN_MEASURED_DAYS:
        return NextSessionRule(calendar, decision_time)
    lag = max(sessions_until_usable(calendar, day, moment, decision_time) for day, moment in seen.items())
    return MeasuredReleaseRule(calendar, decision_time, lag)


class ReleaseTimeRecorder:
    """Checks whether a session's file is published yet and logs each check. Read-only towards the source."""

    def __init__(
        self,
        source: RawFileSource,
        path_for: Callable[[date], str],
        calendar: SessionCalendar,
        log: ReleaseLog,
        clock: Callable[[], datetime] = now_ist,
        sleep: Callable[[float], None] = clock_time.sleep,
    ):
        self.source, self.path_for, self.calendar, self.log = source, path_for, calendar, log
        self.clock, self.sleep = clock, sleep

    def check(self, day: date) -> ReleaseCheck:
        checked_at = self.clock()
        try:
            data = self.source.fetch(self.path_for(day))
        except RawSourceUnavailable:
            check = ReleaseCheck(day, checked_at, RELEASE_UNREACHABLE)
        else:
            outcome = RELEASE_ABSENT if data is None else RELEASE_PRESENT
            check = ReleaseCheck(day, checked_at, outcome, hashlib.sha256(data).hexdigest() if data else "")
        self.log.append(check)
        return check

    def watch(self, day: date, until: datetime, every: timedelta) -> ReleaseCheck | None:
        """Checks every `every` until the file is seen or `until` passes; None when `day` is not a session. A day
        already seen is not asked again."""
        if not self.calendar.is_session(day):
            return None
        seen = [c for c in self.log.checks() if c.day == day and c.outcome == RELEASE_PRESENT]
        if seen:
            return min(seen, key=lambda c: c.checked_at)
        while True:
            check = self.check(day)
            if check.outcome == RELEASE_PRESENT or self.clock() + every > until:
                return check
            self.sleep(every.total_seconds())
