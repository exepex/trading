"""The paper desk's daily run (story E3, design 13.5 steps 4-5): `DailyRun.run(day)` walks the fixed timetable.

1. On a day that is not a recorded session (A7 calendar: closed, or a muhurat-only evening) nothing runs.
2. `versions`: Book 1's D6 version is kept current before any decision (judge 80).
3. `pack` (from about 14:58): E2's common pack, built only once the 3 pm canonical snapshot is committed (judge 72),
   retried until the recorder's window ends.
4. `decisions` (at the deadline): the collector pulls once; each book's run visible then is recorded (run ID, holding
   commit, the origin commit seen); a book without one gets a committed "no decision (late)" and cannot join later.
   A slow book delays nothing: decisions are read, not awaited. Collected after the deadline (a restart), every book is
   late (fail closed).
5. `snapshot` (at the execution time): one capture for every book, with one common retry if it is not valid.
6. `fills`: only the runs recorded at the deadline, each with a completed C4 pass, fill against that one snapshot;
   none if it is invalid.
7. `exits`: every book's exit review, whatever happened before (risk-reducing exits always run).
8. `trade_marks`: every account's open trades valued at the session's snapshot by S2's rule, with its equity row (story
   E2d), so a trade opened or kept today is valued today.

The steps run in the order of `DAILY_RUN_STEPS` (story O1, the one tuple the health check O8 reads): the desk's own
above, and around them O1's `DayStep`s (the margin check, weather, v4 forecasts and the quote parts before, Book 1's
decision after the pack, the parts' results and the card after), each run at once when its turn comes. A name with no
step given (E3's tests) is passed over.

Each step's start, end, inputs and result go to `journal/runs/<date>.json`, committed after the step; a restarted run
skips every step already recorded, so nothing is done twice. A commit that fails (a refused raw quote file, a failed
pull, a push rejected every time) or a git read that fails (`GitFailed`, e.g. the decisions' pull or a run's commit
read in the fills) stops the run at that step: one alert naming why, what is missed and the hand fix, no later step,
nothing more committed, and `RunStopped` for the command to end on one line (decision 44). The rerun
first commits that failed commit's files exactly as they were recorded, and never repeats the step that made them
(`PendingCommitter`, decision 47).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date, datetime, time, timedelta
from pathlib import Path

from ..constants import (
    DAILY_RUN_STEPS,
    OWNER_TIMING_STEP,
    REVIEWS_STEP,
    RUN_LOG_DECISIONS_STEP,
    RUN_LOG_EXITS_STEP,
    RUN_LOG_TRADE_MARKS_STEP,
    STEP_FAILED,
    STEP_REFUSED,
)
from ..quotes.recorder import RECORDED_SESSION_KINDS
from ..research_data.calendar import SessionCalendar
from ..research_engine.ledger import GitFailed
from .daily_ports import CommitFailed, DayStep, Waiter
from .daily_steps import DeskSteps, StepOutcome
from .pending_commit import PendingChanged, PendingCommitter
from .private_files import PrivateFiles
from .run_log import RunLog
from .step_recorder import AsGiven, StepRecorder
from .trade_marking import MarkingStep

SKIPPED = "skipped"
STOPPED = "F&O paper desk {day}: run STOPPED at {where}, no later step runs{missed}: {what}: {reason}. {fix}"
COMMIT_FAILED = "the commit failed"
GIT_FAILED = "a git read failed"
EXITS_MISSED = "; exits not reviewed today"
RERUN = "Fix: remove the cause, then rerun `fno daily run` (it commits these files as recorded, never repeating a step)"
PUSHES = "; the rerun pushes the local commit"
RECOVERY = "the rerun's start"
DOWNLOAD = "the download of the private paper records"
PACK_RETRY = timedelta(seconds=30)
NO_LOG = "the run of {day} stopped before any step"
BEFORE_EXITS = "the run of {day} stopped before its exits"
NOT_REVIEWED = "the exits of {day} were not reviewed ({why})"
HELD_UP = "due exits held up: {exits}"
UNSCORED = "the scorecards and automatic pauses of {day} did not run ({reason})"
UNFILLED = "today's owner-timing fills {status} ({reason})"
# a stop at the exits or any later step leaves the day's exits reviewed (E2d's marking and O1's steps after them)
AFTER_EXITS = tuple(f"step {name}" for name in DAILY_RUN_STEPS[DAILY_RUN_STEPS.index(RUN_LOG_EXITS_STEP) :])


class RunStopped(Exception):
    """The run stopped at a failed commit or git read; the message is the alert sent."""


class DailyRun:
    def __init__(self, steps: DeskSteps, calendar: SessionCalendar, committer: PendingCommitter, waiter: Waiter,
                 clock: Callable[[], datetime], marking: MarkingStep, files: PrivateFiles | None = None,
                 day_steps: Mapping[str, DayStep] | None = None, recorder: StepRecorder | None = None):  # fmt: skip
        self.steps, self.calendar, self.committer, self.waiter, self.clock = steps, calendar, committer, waiter, clock
        self.marking = marking  # story E2d
        self.files = files  # story E2c: the private records in Drive, downloaded before any step reads them
        self.day_steps = dict(day_steps or {})  # story O1's steps around the desk's
        self.recorder = recorder or AsGiven()  # story O1-status-only: the committed log holds status only

    def run(self, day: date) -> RunLog:
        self._guarded(day, RECOVERY, self.committer.recover)
        if self.files is not None:
            self._guarded(day, DOWNLOAD, self.files.download)
        log = RunLog.open(self.steps.root, day)
        kind = self.calendar.session_kind(day)
        if kind not in RECORDED_SESSION_KINDS:
            if not log.done(SKIPPED):
                self._step(log, SKIPPED, lambda: StepOutcome({"session": kind}, {"reason": "not a session day"}))
            return log
        plan = self._plan(day, log)
        for name in DAILY_RUN_STEPS:
            if name in plan and not log.done(name):
                moment, action = plan[name]
                if moment is not None:
                    self.waiter.until(self.steps.timetable.at(day, moment))
                self._step(log, name, action)
        return log

    def _plan(self, day: date, log: RunLog) -> dict[str, tuple[time | None, Callable[[], StepOutcome]]]:
        """Each step by name: when it may start (None: at once, in its turn) and what it does."""
        times, steps = self.steps.timetable, self.steps
        desk = {
            "versions": (times.pack, lambda: steps.keep_versions(day)),
            "pack": (times.pack, lambda: self._pack(day)),
            RUN_LOG_DECISIONS_STEP: (times.decision_deadline, lambda: steps.collect_decisions(day)),
            "snapshot": (times.execution_snapshot, lambda: steps.take_snapshot(day)),
            "fills": (times.execution_snapshot, lambda: steps.fill(day, log.result("snapshot")["valid"],
                                                                   log.result(RUN_LOG_DECISIONS_STEP),
                                                                   self._unreviewed(day) | self._unscored(day)
                                                                   | self._unfilled(log))),
            "exits": (times.execution_snapshot, lambda: steps.review_exits(day)),
            RUN_LOG_TRADE_MARKS_STEP: (times.execution_snapshot, lambda: self.marking.run(day)),  # story E2d
        }  # fmt: skip
        return desk | {name: (None, lambda step=step: step.run(day)) for name, step in self.day_steps.items()}

    def _unreviewed(self, day: date) -> dict[str, str]:
        """Each book whose exits the last session did not review, with why (review 105 point 3, judge 159, review
        115): today it opens nothing new. The routine starts in a fresh container, so the committed run log is the only
        place this can be seen.
        - No log while an earlier one exists: a stop before any step (the recovery or the download). Every book.
        - A log without its exits step: a stop before the exits. Every book.
        - An exits step where a book's review failed (`error`) or exits were due but held up (`waiting`): that book.
          A day without a snapshot and nothing due leaves no exit unreviewed, so it blocks nothing."""
        last = self.calendar.previous_session(day)
        log = RunLog.open(self.steps.root, last)
        if not log.steps:
            stopped = any(d < last for d in RunLog.days(self.steps.root))
            return dict.fromkeys(self.steps.books, NO_LOG.format(day=last)) if stopped else {}
        if SKIPPED in log.steps:
            return {}
        if "exits" not in log.steps:
            return dict.fromkeys(self.steps.books, BEFORE_EXITS.format(day=last))
        unreviewed = {book: r.get("error") or HELD_UP.format(exits="; ".join(r["waiting"]))
                      for book, r in log.result("exits").items() if r.get("error") or r.get("waiting")}  # fmt: skip
        return {book: NOT_REVIEWED.format(day=last, why=why) for book, why in unreviewed.items()}

    def _unfilled(self, log: RunLog) -> dict[str, str]:
        """Story E8 rule 11: when today's owner-timing fills failed or were refused, C2 would see yesterday's positions
        without this morning's fills and understate open risk, so no book opens anything new today (exits still run)."""
        result = log.result(OWNER_TIMING_STEP) if log.done(OWNER_TIMING_STEP) else {}
        if result.get("status") not in (STEP_FAILED, STEP_REFUSED):
            return {}
        reason = result.get("reason", "")  # a status-only log holds the reason's code (O1-status-only)
        return dict.fromkeys(self.steps.books, UNFILLED.format(status=result["status"], reason=reason))

    def _unscored(self, day: date) -> dict[str, str]:
        """Story O1 (judge 214): when the last session reviewed its exits but its scorecards and automatic pauses (E6)
        failed or were refused, a catastrophic loss may be unpaused, so no book opens anything new today (exits run).
        Only once the run has the step (E3's own tests do not)."""
        if REVIEWS_STEP not in self.day_steps:
            return {}
        last = self.calendar.previous_session(day)
        steps = RunLog.open(self.steps.root, last).steps
        if RUN_LOG_EXITS_STEP not in steps:  # no run, a closed day or a stop before the exits: `_unreviewed`'s rule
            return {}
        result = steps.get(REVIEWS_STEP, {}).get("result", {"status": STEP_FAILED, "reason": "not run"})
        if result.get("status") not in (STEP_FAILED, STEP_REFUSED):
            return {}
        return dict.fromkeys(self.steps.books, UNSCORED.format(day=last, reason=result.get("reason", "")))

    def _pack(self, day: date) -> StepOutcome:
        """Retries while the canonical snapshot is not committed yet, until the recorder's window ends."""
        last = self.steps.timetable.at(day, self.steps.timetable.pack_wait_until)
        outcome = self.steps.build_pack(day)
        while not outcome.result["built"] and self.clock() + PACK_RETRY <= last:
            self.waiter.until(self.clock() + PACK_RETRY)
            outcome = self.steps.build_pack(day)
        return outcome

    def _step(self, log: RunLog, name: str, action: Callable[[], StepOutcome]) -> None:
        def step() -> None:
            started = self.clock()
            outcome = action()
            self.recorder.record(log, name, started, self.clock(), outcome.inputs, outcome.result)
            paths: tuple[Path, ...] = (log.path, *outcome.paths)
            self.committer.commit(paths, f"Desk run {log.day} step {name}")

        self._guarded(log.day, f"step {name}", step)

    def _guarded(self, day: date, where: str, action: Callable[[], object]) -> None:
        """The one place a failed commit or git read is handled: the rerun's recovery, a step's own commit and any
        inside it. A git read cannot be trusted to answer later steps either, so it stops the run the same way."""
        try:
            action()
        except CommitFailed as failed:
            fix = "" if isinstance(failed, PendingChanged) else RERUN + (PUSHES if failed.unpushed else "")
            self._stop(day, where, COMMIT_FAILED, failed, fix)
        except GitFailed as failed:
            self._stop(day, where, GIT_FAILED, failed, RERUN)

    def _stop(self, day: date, where: str, what: str, failed: Exception, fix: str) -> None:
        missed = "" if where in AFTER_EXITS else EXITS_MISSED
        text = STOPPED.format(day=day, where=where, missed=missed, what=what, reason=failed, fix=fix).rstrip(" ")
        self.steps.alerts.send(text)
        raise RunStopped(text) from failed
