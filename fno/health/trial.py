"""The go-live trial (owner via the orchestrator, 16 Oct 2026; story O10): 10 sessions in a row with zero silent
failures. A problem (late, missed, unknown) is SILENT unless its job recorded it: the check's evidence holds the job's
own failure record (a `none` canonical, A16's bad mark) or `capture_errors.csv` has a row from one of the check's jobs,
dated the session or up to `MATCH_DAYS` later (evening jobs and late GitHub starts run the next day). Each row excuses
one session only. A `_recovered` row closes an episode and records nothing.

A session is judged once, by the first run at which none of its checks is `not due`, and appended to
`research/ops/trial_days.csv` (never edited). The streak is recomputed from that file and the calendar: a session with
no row (it left the window before it was final, or no health run saw it) is "not proven" and breaks the streak. The
trial therefore depends on health-check.yml's own cron starting at least once every `window_days` (judge 357)."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from ..constants import HEALTH_NOT_DUE, HEALTH_NOT_EXPECTED, HEALTH_PROBLEMS, HEALTH_UNKNOWN
from ..research_data.calendar import SessionCalendar
from .capture_errors import CaptureError, CaptureErrorLog
from .checker import Finding, HealthRun

TRIAL_FILE = "research/ops/trial_days.csv"
COLUMNS = ("session", "silent_count", "silent_checks")
MATCH_DAYS = 1  # evening jobs and late GitHub starts land by the next IST day (measured: 01:52, 11:41, 12:11)
RECOVERED = "_recovered"
TRIAL_LINE = "trial: {count} clean session{s} in a row{why}"


@dataclass(frozen=True)
class TrialDay:
    session: date
    silent: tuple[str, ...]


def judge(run: HealthRun, errors: list[CaptureError]) -> list[TrialDay]:
    """Each session of the run whose checks are all final, with its silent checks (`<check>:<status>`). A session
    nothing checked (no live, expected check) is never judged. An `unknown` may be the health check's own blind spot
    (GitHub's log unreachable), so it waits for the session's last run in the window, where it counts as a problem
    (O8 owner's review)."""
    days, excused = [], _excused(run, errors)
    last_chance = run.run_day - timedelta(days=run.window_days)
    for session in run.sessions:
        found = [f for f in run.findings if f.session == session and f.result.status != HEALTH_NOT_EXPECTED]
        statuses = {f.result.status for f in found}
        if not found or HEALTH_NOT_DUE in statuses or (HEALTH_UNKNOWN in statuses and session > last_chance):
            continue
        silent = [f"{f.check}:{f.result.status}" for f in _problems(found) if (f.check, session) not in excused]
        days.append(TrialDay(session, tuple(silent)))
    return days


def _problems(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.result.status in HEALTH_PROBLEMS and not f.result.recorded]


def _excused(run: HealthRun, errors: list[CaptureError]) -> set[tuple[str, date]]:
    """Each capture-error row excuses ONE problem of its check: the latest not yet excused, dated from `MATCH_DAYS`
    before the row to the row's day (judge 357: one row must never cover a run of silent sessions)."""
    excused: set[tuple[str, date]] = set()
    for check, jobs in run.jobs:
        open_sessions = sorted({f.session for f in _problems([f for f in run.findings if f.check == check])})
        for row in sorted((e for e in errors if e.job in jobs and not e.kind.endswith(RECOVERED)),
                          key=lambda e: e.day, reverse=True):  # fmt: skip
            covered = [s for s in open_sessions if row.day - timedelta(days=MATCH_DAYS) <= s <= row.day]
            if covered:
                excused.add((check, covered[-1]))
                open_sessions.remove(covered[-1])
    return excused


class TrialLedger:
    def __init__(self, path: Path):
        self.path = Path(path)

    def days(self) -> dict[date, TrialDay]:
        if not self.path.is_file():
            return {}
        rows = csv.DictReader(io.StringIO(self.path.read_text(encoding="utf-8")))
        return {d.session: d for d in (_day(row) for row in rows)}

    def new(self, judged: list[TrialDay]) -> list[TrialDay]:
        known = self.days()
        return [day for day in judged if day.session not in known]

    def append(self, days: list[TrialDay]) -> None:
        if not days:
            return
        new = not self.path.is_file()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            if new:
                writer.writerow(COLUMNS)
            for day in days:
                writer.writerow((day.session.isoformat(), len(day.silent), ";".join(day.silent)))


def _day(row: dict) -> TrialDay:
    return TrialDay(date.fromisoformat(row["session"]), tuple(c for c in row["silent_checks"].split(";") if c))


def trial_line(days: dict[date, TrialDay], calendar: SessionCalendar) -> str:
    """The streak back from the last judged session; every calendar session in between must have its row."""
    if not days:
        return "trial: no session judged yet"
    count, day, first = 0, max(days), min(days)
    while day >= first:
        if calendar.is_session(day):
            judged = days.get(day)
            if judged is None:
                return TRIAL_LINE.format(count=count, s="s" * (count != 1), why=f" (not proven: {day:%d %b})")
            if judged.silent:
                why = f" (last silent: {', '.join(judged.silent)} {day:%d %b})"
                return TRIAL_LINE.format(count=count, s="s" * (count != 1), why=why)
            count += 1
        day -= timedelta(days=1)
    return TRIAL_LINE.format(count=count, s="s" * (count != 1), why="")


class TrialReport:
    """The health message's trial lines, and the sessions a real run appends (never a dry run: the CLI decides)."""

    def __init__(self, ledger: TrialLedger, errors: CaptureErrorLog, calendar: SessionCalendar):
        self.ledger, self.errors, self.calendar = ledger, errors, calendar
        self.fresh: list[TrialDay] = []

    def lines(self, run: HealthRun) -> list[str]:
        errors = self.errors.rows()
        self.fresh = self.ledger.new(judge(run, errors))
        days = {**self.ledger.days(), **{d.session: d for d in self.fresh}}
        found = errors_line(errors, run.sessions[0], run.run_day) if run.sessions else None
        return [*([found] if found else []), trial_line(days, self.calendar)]

    def record(self) -> None:
        self.ledger.append(self.fresh)


def errors_line(errors: list[CaptureError], first: date, last: date) -> str | None:
    """One line naming the window's capture errors (recoveries aside), or None when there are none."""
    found = [e for e in errors if first <= e.day <= last and not e.kind.endswith(RECOVERED)]
    if not found:
        return None
    return f"capture errors: {len(found)} in the window ({', '.join(sorted({e.job for e in found}))})"
