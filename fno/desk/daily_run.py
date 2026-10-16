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

Each step's start, end, inputs and result go to `journal/runs/<date>.json`, committed after the step; a restarted run
skips every step already recorded, so nothing is done twice. A commit that fails (a refused raw quote file, a failed
pull, a push rejected every time) stops the run at that step: one alert naming why, what is missed and the hand fix,
no later step, nothing more committed, and `RunStopped` for the command to end on one line (decision 44). The rerun
first commits that failed commit's files exactly as they were recorded, and never repeats the step that made them
(`PendingCommitter`, decision 47).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta
from pathlib import Path

from ..constants import RUN_LOG_DECISIONS_STEP
from ..quotes.recorder import RECORDED_SESSION_KINDS
from ..research_data.calendar import SessionCalendar
from .daily_ports import CommitFailed, Waiter
from .daily_steps import DeskSteps, StepOutcome
from .pending_commit import PendingChanged, PendingCommitter
from .private_files import PrivateFiles
from .run_log import RunLog

SKIPPED = "skipped"
STOPPED = "F&O paper desk {day}: run STOPPED at {where}, no later step runs{missed}: the commit failed: {reason}. {fix}"
EXITS_MISSED = "; exits not reviewed today"
RERUN = "Fix: remove the cause, then rerun `fno desk run` (it commits these files as recorded, never repeating a step)"
PUSHES = "; the rerun pushes the local commit"
RECOVERY = "the rerun's start"
DOWNLOAD = "the download of the private paper records"
PACK_RETRY = timedelta(seconds=30)
NO_LOG = "the run of {day} stopped before any step"
BEFORE_EXITS = "the run of {day} stopped before its exits"
NOT_REVIEWED = "the exits of {day} were not reviewed ({why})"
HELD_UP = "due exits held up: {exits}"


class RunStopped(Exception):
    """The run stopped at a failed commit; the message is the alert sent."""


class DailyRun:
    def __init__(self, steps: DeskSteps, calendar: SessionCalendar, committer: PendingCommitter, waiter: Waiter,
                 clock: Callable[[], datetime], files: PrivateFiles | None = None):  # fmt: skip
        self.steps, self.calendar, self.committer, self.waiter, self.clock = steps, calendar, committer, waiter, clock
        self.files = files  # story E2c: the private records in Drive, downloaded before any step reads them

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
        times, steps = self.steps.timetable, self.steps
        plan = (
            ("versions", times.pack, lambda: steps.keep_versions(day)),
            ("pack", times.pack, lambda: self._pack(day)),
            (RUN_LOG_DECISIONS_STEP, times.decision_deadline, lambda: steps.collect_decisions(day)),
            ("snapshot", times.execution_snapshot, lambda: steps.take_snapshot(day)),
            (
                "fills",
                times.execution_snapshot,
                lambda: steps.fill(
                    day,
                    log.result("snapshot")["valid"],
                    log.result(RUN_LOG_DECISIONS_STEP),
                    self._unreviewed(day),
                ),
            ),  # fmt: skip
            ("exits", times.execution_snapshot, lambda: steps.review_exits(day)),
        )
        for name, moment, action in plan:
            if not log.done(name):
                self.waiter.until(times.at(day, moment))
                self._step(log, name, action)
        return log

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
            log.record(name, started, self.clock(), outcome.inputs, outcome.result)
            paths: tuple[Path, ...] = (log.path, *outcome.paths)
            self.committer.commit(paths, f"Desk run {log.day} step {name}")

        self._guarded(log.day, f"step {name}", step)

    def _guarded(self, day: date, where: str, action: Callable[[], object]) -> None:
        """The one place a failed commit is handled: the rerun's recovery, a step's own commit and any inside it."""
        try:
            action()
        except CommitFailed as failed:
            missed = "" if where == "step exits" else EXITS_MISSED
            fix = "" if isinstance(failed, PendingChanged) else RERUN + (PUSHES if failed.unpushed else "")
            text = STOPPED.format(day=day, where=where, missed=missed, reason=failed, fix=fix).rstrip(" ")
            self.steps.alerts.send(text)
            raise RunStopped(text) from failed
