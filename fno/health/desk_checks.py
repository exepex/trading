"""The paper desk's daily run (E3) and A16's 15-minute marks.

- Desk: `journal/runs/<date>.json` holds every step of `DAILY_RUN_STEPS` (story O1's tuple, the one the run loops
  over); the `decisions` step finished by the timetable's decision deadline (its in-file time); an O1 step whose status
  is `failed` or `refused` is a problem shown with its reason, `not_live` is present and counts as neither; a `skipped`
  run (not a session day) is not expected, and so is a frozen desk (story O1-desk-freeze: its decisions step is
  `frozen`), unless another step failed.
- A16: the day's ledger has every mark with status `good`. A16's own per-mark status (its 120 s rule) is final: this
  check only counts it, with no deadline of its own beyond the session's last mark."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from ..constants import (
    DAILY_RUN_STEPS,
    HEALTH_LATE,
    HEALTH_MISSED,
    HEALTH_NOT_EXPECTED,
    HEALTH_OK,
    RUN_LOG_DECISIONS_STEP,
    STEP_FAILED,
    STEP_FROZEN,
    STEP_REFUSED,
)
from ..desk.run_log import RunLog
from ..intraday.ledger import SlotLedger
from ..intraday.slots import FIRST_MARK, MARK_STEP, MARKS_PER_SESSION
from ..intraday.status import GOOD, LATE
from ..models import IST
from .model import CheckResult, Deadline, EvidenceUnknown, SessionCheck, absent, judged

SKIPPED_STEP = "skipped"  # the run's closed-day step
DESK_FROZEN = "desk frozen by the owner: no decisions expected"


class RunLogCheck(SessionCheck):
    def __init__(self, root: Path, deadline: Deadline):
        self.root, self.deadline = Path(root), deadline

    def check(self, session: date, now: datetime) -> CheckResult:
        log = RunLog.open(self.root, session)
        if not log.steps:
            return absent(now, self.deadline.on(session), "never ran: no run log")
        if log.done(SKIPPED_STEP):
            return CheckResult(HEALTH_NOT_EXPECTED, "run skipped: not a session day")
        if not log.done(RUN_LOG_DECISIONS_STEP):
            return absent(now, self.deadline.on(session), "no decisions step")
        if log.result(RUN_LOG_DECISIONS_STEP).get("status") == STEP_FROZEN:
            problems = _problems(log)
            return CheckResult(HEALTH_MISSED, problems) if problems else CheckResult(HEALTH_NOT_EXPECTED, DESK_FROZEN)
        try:
            decided = datetime.fromisoformat(log.steps[RUN_LOG_DECISIONS_STEP]["finished_at"])
        except (KeyError, TypeError, ValueError):
            raise EvidenceUnknown(f"{log.path.name}: the decisions step has no readable finish time") from None
        result = judged(decided, self.deadline.on(session), "decisions finished")
        problems = _problems(log)
        if result.status == HEALTH_OK and problems:
            return CheckResult(HEALTH_MISSED, problems)
        return result


def _problems(log: RunLog) -> str:
    """Steps not run, and O1 steps that failed or were refused with their reasons; empty when there are none."""
    missing = [step for step in DAILY_RUN_STEPS if not log.done(step)]
    results = {name: step["result"] for name, step in log.steps.items()}
    bad = [f"{name} {r['status']}: {r.get('reason', '')}" for name, r in results.items()
           if r.get("status") in (STEP_FAILED, STEP_REFUSED)]  # fmt: skip
    parts = ([f"steps not run: {', '.join(missing)}"] if missing else []) + (
        [f"steps not ok: {'; '.join(bad)}"] if bad else []
    )
    return "; ".join(parts)


class MarksCheck(SessionCheck):
    def __init__(self, folder: Path):
        self.ledger = SlotLedger(folder)

    def check(self, session: date, now: datetime) -> CheckResult:
        last_mark = datetime.combine(session, FIRST_MARK, IST) + MARK_STEP * (MARKS_PER_SESSION - 1)
        rows = self.ledger.rows(session)
        if not rows:
            return absent(now, last_mark, "no marks")
        good = sum(1 for row in rows if row.get("status") == GOOD)
        late = sum(1 for row in rows if row.get("status") == LATE)
        if good == MARKS_PER_SESSION:
            return CheckResult(HEALTH_OK, f"{good} of {MARKS_PER_SESSION} good")
        detail = f"{good} of {MARKS_PER_SESSION} good, {late} late, {MARKS_PER_SESSION - good - late} other"
        if now < last_mark:
            return absent(now, last_mark, detail)
        return CheckResult(HEALTH_LATE if good + late == MARKS_PER_SESSION else HEALTH_MISSED, detail)
