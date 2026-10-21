"""`python -m fno preopen record` (story A22): on a trading day, reads the four parts in their windows, saves each
part's answer write-once to Drive as soon as it ends, writes the day row once, appends one O10 capture-error row per
problem, commits the receipts and the rows (by 09:12 IST) and posts one #fno-desk line naming every problem. Lines
name parts, statuses and exception kinds only, never a value."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date

from ..alerts.sender import AlertSender
from ..health.capture_errors import CaptureError, CaptureErrorLog
from ..research_data.calendar import CalendarError
from ..storage.data_store import DataStore
from ..storage.manifest_commit import ManifestRecorder
from ..storage.raw_store import RawFileConflict
from .day_row import day_file, day_row, raw_file
from .run import OK, PartResult, PreopenRun

JOB = "preopen"
NOT_TRADING = "not a trading day"
PART_LINE = "{part} {status} ({reads} read(s)){detail}"
DONE, WITH_PROBLEMS = "pre-open recorded", "pre-open recorded with problems: {problems}"
ALERT = "A22 pre-open capture {day}: {problems}"
NOT_COMMITTED = " NOT committed"
DAY_ROW_TAKEN = "day row already written by an earlier run; this run's row not kept"
SAVE_ERRORS = (OSError, RuntimeError, ValueError)  # Drive and its settings; RawFileConflict is a RuntimeError


@dataclass(frozen=True)
class Problem:
    step: str
    kind: str
    message: str

    def line(self) -> str:
        return f"{self.step} {self.kind}: {self.message}" if self.message else f"{self.step} {self.kind}"


class PreopenRecorder:
    def __init__(self, is_trading_day: Callable[[date], bool], run: Callable[[Callable], PreopenRun],
                 store: DataStore, errors: CaptureErrorLog, committers: Sequence[ManifestRecorder],
                 alerts: AlertSender, clock_warning: Callable[[], str], out=print):  # fmt: skip
        """`run`: builds the window run around the callback that saves each finished part."""
        self.is_trading_day, self.build_run, self.store, self.errors = is_trading_day, run, store, errors
        self.committers, self.alerts, self.clock_warning, self.out = committers, alerts, clock_warning, out

    def record(self, day: date) -> int:
        try:
            if not self.is_trading_day(day):
                self.out(NOT_TRADING)
                return 0
        except CalendarError as error:
            return self._finish(day, [Problem("calendar", "stopped", str(error))])
        problems = [Problem("clock", "warning", warning)] if (warning := self.clock_warning()) else []
        results = self.build_run(lambda result: problems.extend(self._save_raw(day, result))).run(day)
        for result in results:
            self.out(PART_LINE.format(part=result.part, status=result.status, reads=result.reads,
                                      detail=f": {result.detail}" if result.detail else ""))  # fmt: skip
        problems += [Problem(r.part, r.status, r.detail) for r in results if r.status != OK]
        problems += self._save_day_row(day, warning or "ok", results)
        return self._finish(day, problems)

    def _save_raw(self, day: date, result: PartResult) -> list[Problem]:
        if result.answer is None:
            return []
        try:
            self.store.put(raw_file(day, result), result.answer.raw)
        except SAVE_ERRORS as error:
            return [Problem(result.part, "raw not saved to Drive", type(error).__name__)]
        return []

    def _save_day_row(self, day: date, clock: str, results: list[PartResult]) -> list[Problem]:
        try:
            self.store.put(day_file(day), day_row(day, clock, results))
        except RawFileConflict:
            return [Problem("day row", "taken", DAY_ROW_TAKEN)]
        except SAVE_ERRORS as error:
            return [Problem("day row", "not saved to Drive", type(error).__name__)]
        return []

    def _finish(self, day: date, problems: list[Problem]) -> int:
        for problem in problems:
            self.errors.append(CaptureError(day, JOB, problem.step, problem.kind, problem.message, ""))
        for committer in self.committers:
            outcome = committer.commit(f"pre-open {day}")
            self.out(outcome)
            if NOT_COMMITTED in outcome:
                problems.append(Problem("commit", "failed", outcome))
        if not problems:
            self.out(DONE)
            return 0
        lines = "; ".join(problem.line() for problem in problems)
        self.out(WITH_PROBLEMS.format(problems=lines))
        self.out(self.alerts.send(ALERT.format(day=day, problems=lines)))
        return 1
