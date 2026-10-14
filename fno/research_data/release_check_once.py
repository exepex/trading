"""One scheduled check of NSE's participant-OI file (story A8 on GitHub Actions, no AI session). A job started every
15 minutes in the evening runs this once and exits, instead of one process watching for hours.

- NSE's session calendar decides the day; a closed day checks nothing.
- Once the day's file is recorded present, later runs that day check nothing.
- The last few seen files are re-read for rewrites at most once a day: the log itself shows whether a run today already
  did (a check made today for an earlier day).
- It returns the alerts for the owner: a rewritten file, NSE unreachable, and the file still absent at the first check
  from `LATE_FROM` IST (the evening's last runs, or any later one), once a day.
- GitHub starts scheduled runs late (14 Oct 2026: 4.5 to 5.5 hours, and some never), so a run may start after midnight:
  before `DUE_FROM` IST it checks the previous day's file, the one still due, never the next day's (`due_day`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from ..constants import RELEASE_ABSENT, RELEASE_REWRITTEN, RELEASE_UNREACHABLE
from .release_times import ReleaseCheck, ReleaseTimeRecorder

LATE_FROM = time(23, 15)
DUE_FROM = time(12, 0)  # NSE publishes in the evening: a morning run is a late run of the evening before
NOT_SESSION = "{day}: not a trading day; nothing checked"
ALREADY = "{day}: already recorded present at {at:%H:%M} IST; nothing checked"
CHECKED = "{day}: {outcome} at {at:%Y-%m-%d %H:%M} IST {sha}"
REWRITTEN = "Omenix F&O participant OI: REWRITTEN {day}: NSE's file changed after it was first seen (now {sha})"
UNREACHABLE = "Omenix F&O participant OI: NSE's archive was unreachable at {at:%Y-%m-%d %H:%M} IST for the {day} file"
STILL_ABSENT = "Omenix F&O participant OI: the {day} file is still absent at {at:%Y-%m-%d %H:%M} IST, past {late:%H:%M}"


def due_day(now: datetime) -> date:
    """The day whose file a run at `now` (IST) checks: today from `DUE_FROM`, else yesterday."""
    return now.date() if now.time() >= DUE_FROM else now.date() - timedelta(days=1)


@dataclass
class CheckOnceResult:
    lines: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)


class ReleaseCheckOnce:
    def __init__(self, recorder: ReleaseTimeRecorder, late_from: time = LATE_FROM):
        self.recorder, self.late_from = recorder, late_from

    def run(self, day: date) -> CheckOnceResult:
        result = CheckOnceResult()
        if not self.recorder.calendar.is_session(day):
            result.lines.append(NOT_SESSION.format(day=day))
            return result
        if not self._rechecked_on(day):
            for check in self.recorder.recheck_recent(day):
                if check.outcome == RELEASE_REWRITTEN:
                    result.alerts.append(REWRITTEN.format(day=check.day, sha=check.sha256[:12]))
        seen = self.recorder.first_present(day)
        if seen:
            result.lines.append(ALREADY.format(day=day, at=seen.checked_at))
            return result
        check = self.recorder.check(day)
        result.lines.append(CHECKED.format(day=day, outcome=check.outcome, at=check.checked_at, sha=check.sha256[:12]))
        if check.outcome == RELEASE_UNREACHABLE:
            result.alerts.append(UNREACHABLE.format(day=day, at=check.checked_at))
        elif check.outcome == RELEASE_ABSENT and self._first_late_check(check):
            result.alerts.append(STILL_ABSENT.format(day=day, at=check.checked_at, late=self.late_from))
        return result

    def _rechecked_on(self, day: date) -> bool:
        return any(c.day < day and c.checked_at.date() == day for c in self.recorder.log.checks())

    def _first_late_check(self, check: ReleaseCheck) -> bool:
        late_from = datetime.combine(check.day, self.late_from, check.checked_at.tzinfo)
        if check.checked_at < late_from:
            return False
        late = [c for c in self.recorder.log.checks() if c.day == check.day and c.checked_at >= late_from]
        return min(late, key=lambda c: c.checked_at) == check
