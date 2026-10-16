"""One run of A20b's job: read the circulars already listed (verified Drive cache), capture the feeds, commit the
receipts. Any problem makes one #fno-desk alert naming every problem, and the run exits 1."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date

from ..alerts.sender import AlertSender
from ..storage.manifest_commit import ManifestRecorder
from .capture import CircularCapture

NOT_COMMITTED_MARK = " NOT committed"
SEEN_FAILED = "earlier circulars NOT read, nothing captured (a capture now would list them again): {error}"
LIST_NOT_SAVED = "the run's new circulars NOT saved to Drive (the next run lists them again): {error}"
ALERT = "Omenix F&O circulars {day}: NOT complete: {problems}. Run log: {where}"


class CircularsJob:
    def __init__(self, seen: Callable[[], Mapping[str, str]], capture: CircularCapture, committer: ManifestRecorder,
                 alerts: AlertSender, where: str, out=print):  # fmt: skip
        self.seen, self.capture, self.committer = seen, capture, committer
        self.alerts, self.where, self.out = alerts, where, out

    def run(self, day: date) -> int:
        """0 when every feed was read and every relevant file saved; 1 (after one alert) otherwise."""
        try:
            seen = self.seen()
        except (RuntimeError, ValueError) as exc:  # Drive, a missing or damaged earlier part
            problems = [SEEN_FAILED.format(error=exc)]
        else:
            problems = self._capture(day, seen)
        committed = self.committer.commit(f"circulars {day}")
        self.out(committed)
        if NOT_COMMITTED_MARK in committed:
            problems.append(committed)
        for line in problems:
            self.out(line)
        if not problems:
            return 0
        self.out(self.alerts.send(ALERT.format(day=day, problems="; ".join(problems), where=self.where)))
        return 1

    def _capture(self, day: date, seen: Mapping[str, str]) -> list[str]:
        try:
            return self.capture.run(day, seen)
        except (RuntimeError, ValueError) as exc:  # the run's list part could not be saved to Drive
            return [LIST_NOT_SAVED.format(error=exc)]
