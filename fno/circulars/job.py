"""One run of A20b's job: read the circulars already listed (verified Drive cache), capture the feeds, commit the
receipts and the open-problem keys. An hourly job alerts once per episode: a new problem posts one line naming every
new problem, a known one posts nothing (the step still counts as having spoken), a cleared one posts one "recovered"
line. Any open problem makes the run exit 1, so O10's watcher records every failed run."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date

from ..alerts.sender import AlertSender
from ..storage.manifest_commit import ManifestRecorder
from .capture import CircularCapture
from .episodes import OpenProblems
from .model import Problem

NOT_COMMITTED_MARK = " NOT committed"
SEEN_FAILED = "earlier circulars NOT read, nothing captured (a capture now would list them again): {error}"
LIST_NOT_SAVED = "the run's new circulars NOT saved to Drive (the next run lists them again): {error}"
ALERT = "Omenix F&O circulars {day}: NOT complete: {problems}. Run log: {where}"
ALREADY = "already alerted, still open: {keys}"
RECOVERED = "Omenix F&O circulars {day}: recovered: {keys}"


class CircularsJob:
    def __init__(self, seen: Callable[[], Sequence[dict]], capture: CircularCapture,
                 committers: Sequence[ManifestRecorder], state: OpenProblems, alerts: AlertSender,
                 spoken: Callable[[], None], where: str, out=print):  # fmt: skip
        self.seen, self.capture, self.committers, self.state = seen, capture, committers, state
        self.alerts, self.spoken, self.where, self.out = alerts, spoken, where, out

    def run(self, day: date) -> int:
        """0 when nothing is wrong; 1 while any problem is open (alerted once per episode)."""
        problems = self._problems(day)
        before, open_now = self.state.read(), {p.key for p in problems if p.episode}
        self.state.write(open_now)
        problems += [Problem(line, line, episode=False) for line in self._commit(day) if NOT_COMMITTED_MARK in line]
        for problem in problems:
            self.out(problem.text)
        if cleared := sorted(before - open_now):
            self.out(self.alerts.send(RECOVERED.format(day=day, keys=", ".join(cleared))))
        new = [p.text for p in problems if not p.episode or p.key not in before]
        if new:
            self.out(self.alerts.send(ALERT.format(day=day, problems="; ".join(new), where=self.where)))
        elif problems:
            self.out(ALREADY.format(keys=", ".join(sorted(open_now))))
            self.spoken()  # known problems: the workflow's own failure line must stay quiet too
        return 1 if problems else 0

    def _problems(self, day: date) -> list[Problem]:
        try:
            rows = self.seen()
        except (OSError, RuntimeError, ValueError) as exc:  # Drive (requests errors are OSError), a damaged part
            return [Problem("earlier-parts", SEEN_FAILED.format(error=exc))]
        try:
            return self.capture.run(day, rows)
        except (OSError, RuntimeError, ValueError) as exc:  # the run's list part could not be saved to Drive
            return [Problem("list-part", LIST_NOT_SAVED.format(error=exc))]

    def _commit(self, day: date) -> list[str]:
        lines = [committer.commit(f"circulars {day}") for committer in self.committers]
        for line in lines:
            self.out(line)
        return lines
