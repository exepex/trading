"""Measures when NSE first publishes a session's file, and sets the availability rule from that evidence (story A8).

The recorder checks the archive on a schedule and appends every check to a committed log (`day, checked_at, outcome,
sha256, last_modified`); it never edits a row. A day counts as measured only when the log shows its file absent and
later present, so the release falls between two checks. The first `present` time is used: an upper bound on the real
release, the safe side for look-ahead. Until `MIN_MEASURED_DAYS` days are measured, the default next-session rule
applies.

Each `present` check also stores the source's Last-Modified time, and every run re-reads the last few seen files: a
file whose bytes change is logged `rewritten` (NSE rewrites some files after publishing them, judge 15), and the
rewritten bytes are usable no earlier than their own last write (`LastWriteBoundRule`).
"""

from __future__ import annotations

import csv
import hashlib
import time as clock_time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

from ..constants import RELEASE_ABSENT, RELEASE_PRESENT, RELEASE_REWRITTEN, RELEASE_UNREACHABLE
from ..models import now_ist
from ..storage.raw_source import PublishedFile, RawFileSource, RawSourceUnavailable
from .availability import AvailabilityRule, MeasuredReleaseRule, NextSessionRule, sessions_until_usable
from .calendar import SessionCalendar

LOG_FIELDS = ("day", "checked_at", "outcome", "sha256", "last_modified")
MIN_MEASURED_DAYS = 20
RECHECK_SESSIONS = 5  # each run re-reads the last few seen files, so a rewrite soon after release is caught


@dataclass(frozen=True)
class ReleaseCheck:
    day: date
    checked_at: datetime
    outcome: str  # RELEASE_PRESENT, RELEASE_ABSENT, RELEASE_UNREACHABLE (says nothing) or RELEASE_REWRITTEN
    sha256: str = ""
    last_modified: datetime | None = None  # the source's own last-write time for the bytes seen


class ReleaseLog:
    """The append-only CSV of checks."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def checks(self) -> list[ReleaseCheck]:
        if not self.path.is_file():
            return []
        return [_check_from(row) for row in csv.DictReader(self.path.read_text(encoding="utf-8").splitlines())]

    def append(self, check: ReleaseCheck) -> None:
        new = not self.path.is_file()
        if not new and self.path.read_text(encoding="utf-8").split("\n", 1)[0] != ",".join(LOG_FIELDS):
            raise ValueError(f"{self.path.name}: its header is not {','.join(LOG_FIELDS)}; nothing appended")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, lineterminator="\n")
            if new:
                writer.writerow(LOG_FIELDS)
            written = check.last_modified.isoformat() if check.last_modified else ""
            writer.writerow([check.day.isoformat(), check.checked_at.isoformat(), check.outcome, check.sha256, written])


def _check_from(row: dict[str, str]) -> ReleaseCheck:
    written = row["last_modified"]
    return ReleaseCheck(
        date.fromisoformat(row["day"]),
        datetime.fromisoformat(row["checked_at"]),
        row["outcome"],
        row["sha256"],
        datetime.fromisoformat(written) if written else None,
    )


def last_written_times(checks: list[ReleaseCheck]) -> dict[date, datetime]:
    """Day -> the latest last-write time the source reported for that day's file."""
    latest: dict[date, datetime] = {}
    for c in checks:
        if c.last_modified and (c.day not in latest or c.last_modified > latest[c.day]):
            latest[c.day] = c.last_modified
    return latest


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
        """One check, logged. A file whose bytes differ from the first ones seen for that day is logged `rewritten`."""
        checked_at = self.clock()
        try:
            found = self.source.fetch_published(self.path_for(day))
        except RawSourceUnavailable:
            check = ReleaseCheck(day, checked_at, RELEASE_UNREACHABLE)
        else:
            check = self._outcome(day, checked_at, found)
        self.log.append(check)
        return check

    def _outcome(self, day: date, checked_at: datetime, found: PublishedFile | None) -> ReleaseCheck:
        if found is None:
            return ReleaseCheck(day, checked_at, RELEASE_ABSENT)
        sha = hashlib.sha256(found.data).hexdigest()
        first = self._first_present(day)
        outcome = RELEASE_REWRITTEN if first and first.sha256 != sha else RELEASE_PRESENT
        return ReleaseCheck(day, checked_at, outcome, sha, found.last_modified)

    def _first_present(self, day: date) -> ReleaseCheck | None:
        seen = [c for c in self.log.checks() if c.day == day and c.outcome == RELEASE_PRESENT]
        return min(seen, key=lambda c: c.checked_at) if seen else None

    def recheck_recent(self, today: date) -> list[ReleaseCheck]:
        """Re-reads the files of the last `RECHECK_SESSIONS` sessions before `today` that were already seen."""
        day, checks = today, []
        for _ in range(RECHECK_SESSIONS):
            day = self.calendar.previous_session(day)
            if self._first_present(day):
                checks.append(self.check(day))
        return checks

    def watch(self, day: date, until: datetime, every: timedelta) -> ReleaseCheck | None:
        """Checks every `every` until the file is seen or `until` passes; None when `day` is not a session. A day
        already seen is not asked again."""
        if not self.calendar.is_session(day):
            return None
        seen = self._first_present(day)
        if seen:
            return seen
        while True:
            check = self.check(day)
            if check.outcome == RELEASE_PRESENT or self.clock() + every > until:
                return check
            self.sleep(every.total_seconds())
