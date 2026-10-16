"""One run of A20a's job: on a trading day, the ban list (filed under the trade date it names; stale refused) and
today's market lots go to Drive with their manifest rows. Each step prints one line; any failed step makes one
#fno-desk alert naming every failure, and the run exits 1."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date

from ..alerts.sender import AlertSender
from ..research_data.calendar import SessionCalendar
from ..storage.manifest_commit import ManifestRecorder
from ..storage.raw_source import RawSourceUnavailable
from ..storage.snapshot_taker import NOT_SERVED

TRADING_KINDS = ("regular", "special")  # a muhurat-only evening is not a day these rules are set for
NOT_A_TRADING_DAY = "{day}: not a trading day; nothing taken"
STEP_OK, STEP_FAILED = "{name}: ok: {line}", "{name}: failed: {reason}"
NOT_COMMITTED_MARK = " NOT committed"
ALERT = "Omenix F&O master files for {day}: NOT complete: {failures}. Run log: {where}"
NOT_SERVED_SUFFIX = NOT_SERVED.removeprefix("{path}")  # a taker's line for a 404: today's copy is missing


@dataclass(frozen=True)
class Step:
    name: str
    run: Callable[[date], str]  # one line on success; raises on a failure


class StepFailed(RuntimeError):
    """A step's own verdict that it did not finish (e.g. NSE did not serve today's file)."""


def taken(line: str) -> str:
    """A taker's line, or StepFailed when NSE did not serve the file (a missing daily rule is a failure, not news)."""
    if line.endswith(NOT_SERVED_SUFFIX):
        raise StepFailed(line)
    return line


class FoMastersJob:
    def __init__(self, calendar: SessionCalendar, steps: Sequence[Step], recorder: ManifestRecorder,
                 alerts: AlertSender, where: str, out=print):  # fmt: skip
        self.calendar, self.steps, self.recorder = calendar, steps, recorder
        self.alerts, self.where, self.out = alerts, where, out

    def run(self, day: date) -> int:
        """0 when every step succeeded or the day is not a trading day; 1 (after one alert) otherwise."""
        if self.calendar.session_kind(day) not in TRADING_KINDS:
            self.out(NOT_A_TRADING_DAY.format(day=day))
            return 0
        failures = [failure for step in self.steps if (failure := self._run(step, day))]
        committed = self.recorder.commit(f"fo-masters {day}")
        self.out(committed)
        if NOT_COMMITTED_MARK in committed:
            failures.append(committed)
        if not failures:
            return 0
        self.out(self.alerts.send(ALERT.format(day=day, failures="; ".join(failures), where=self.where)))
        return 1

    def _run(self, step: Step, day: date) -> str | None:
        try:
            self.out(STEP_OK.format(name=step.name, line=step.run(day)))
            return None
        except (RawSourceUnavailable, ValueError, RuntimeError) as exc:  # Drive, NSE, a check, a stale copy
            line = STEP_FAILED.format(name=step.name, reason=exc)
            self.out(line)
            return line
