"""One run of A20c's job (daily): snapshot every release calendar, commit the receipts; any problem makes one
#fno-desk alert naming every problem, and the run exits 1 (O10's watcher records the failed run)."""

from __future__ import annotations

from datetime import date

from ..alerts.sender import AlertSender
from ..storage.manifest_commit import ManifestRecorder
from .capture import CalendarCapture

NOT_COMMITTED_MARK = " NOT committed"
ALERT = "Omenix F&O macro calendar {day}: NOT complete: {problems}. Run log: {where}"


class MacroCalendarJob:
    def __init__(self, capture: CalendarCapture, committer: ManifestRecorder, alerts: AlertSender, where: str,
                 out=print):  # fmt: skip
        self.capture, self.committer, self.alerts, self.where, self.out = capture, committer, alerts, where, out

    def run(self, day: date) -> int:
        problems = self.capture.run(day)
        committed = self.committer.commit(f"macro-calendar {day}")
        self.out(committed)
        if NOT_COMMITTED_MARK in committed:
            problems.append(committed)
        for problem in problems:
            self.out(problem)
        if not problems:
            return 0
        self.out(self.alerts.send(ALERT.format(day=day, problems="; ".join(problems), where=self.where)))
        return 1
