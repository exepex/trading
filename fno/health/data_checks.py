"""The evening data jobs: the session's row (or the panel's day) is committed, and GitHub received the commit that first
added it by the job's deadline. These deadlines have no owner elsewhere in `fno/`: they live in `expectations.py`."""

from __future__ import annotations

import csv
import io
from datetime import date, datetime

from ..constants import HEALTH_MISSED
from .evidence import Evidence
from .model import CheckResult, Deadline, SessionCheck, absent, judged


class SessionRowCheck(SessionCheck):
    """A CSV with the session date in its `column` (by header name): participant OI, index closes, FII/DII flows,
    NSE margins (`as_of`, its last column) and the market archive's manifests."""

    def __init__(self, evidence: Evidence, path: str, deadline: Deadline, column: str = "date"):
        self.evidence, self.path, self.deadline, self.column = evidence, path, deadline, column

    def check(self, session: date, now: datetime) -> CheckResult:
        day = session.isoformat()
        rows = csv.DictReader(io.StringIO(self.evidence.text(self.path) or ""))
        if not any(row.get(self.column) == day for row in rows):
            return absent(now, self.deadline.on(session), f"no row in {self.path.rsplit('/', 1)[1]}")
        return judged(self.evidence.row_pushed_at(self.path, self._key(rows.fieldnames, day), session),
                      self.deadline.on(session), "pushed")  # fmt: skip

    def _key(self, columns: list[str], day: str) -> str:
        """The text git's pickaxe looks for: the date with the comma(s) beside it in its column's position."""
        position = columns.index(self.column)
        return f"{day}," if position == 0 else f",{day}" if position == len(columns) - 1 else f",{day},"


class PanelDayCheck(SessionCheck):
    """The NIFTY panel's manifest: the session is among its days, with status ok."""

    def __init__(self, evidence: Evidence, path: str, deadline: Deadline):
        self.evidence, self.path, self.deadline = evidence, path, deadline

    def check(self, session: date, now: datetime) -> CheckResult:
        day = ((self.evidence.json(self.path) or {}).get("days") or {}).get(session.isoformat())
        if day is None:
            return absent(now, self.deadline.on(session), "not in the panel")
        if day.get("status") != "ok":
            return CheckResult(HEALTH_MISSED, f"panel status {day.get('status')}")
        pushed = self.evidence.row_pushed_at(self.path, f'"{session.isoformat()}": {{', session)
        return judged(pushed, self.deadline.on(session), "pushed")
