"""The daily run's reviews after the exits (story O1, judge 214): E6's scorecards with their automatic pauses (the
catastrophic and cumulative-loss rules) run every session, marked at the day's execution snapshot, and their status
changes are committed. LR3's drift monitor joins as a second `Review` in the same step. Without a valid snapshot the
open positions cannot be marked, so a catastrophic loss on them cannot be judged: the step is refused, and the next
session opens nothing new (`DailyRun._unscored`). Paper and research only: a pause never places an order."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sequence
from datetime import date
from pathlib import Path

from ..constants import STEP_OK, STEP_REFUSED
from ..desk.daily_ports import DayStep
from ..desk.daily_steps import StepOutcome
from ..desk.run_log import RunLog
from ..desk.snapshot import ExecutionSnapshotSource
from ..scorecard.run import ScorecardRun
from ..scorecard.scorecard import snapshot_marks

SNAPSHOT_STEP = "snapshot"
UNMARKED = "no valid execution snapshot today: open positions cannot be marked, so their loss rules were not judged"


class Review(ABC):
    @abstractmethod
    def review(self, day: date, marks: Mapping) -> list[str]:
        """Judges the day at these marks; one line per finding or action (a pause, an alert)."""


class ScorecardReview(Review):
    def __init__(self, run: ScorecardRun):
        self.run = run

    def review(self, day: date, marks: Mapping) -> list[str]:
        cards, actions = self.run.run(day, marks, pause=True)
        return [f"{len(cards)} scorecards", *actions]


class ReviewsStep(DayStep):
    def __init__(self, reviews: Sequence[Review], snapshots: ExecutionSnapshotSource, root: Path,
                 changed: Callable[[Sequence[str]], list], pathspecs: Sequence[str]):  # fmt: skip
        self.reviews, self.snapshots, self.root, self.changed, self.pathspecs = (
            reviews, snapshots, Path(root), changed, pathspecs)  # fmt: skip

    def run(self, day: date) -> StepOutcome:
        log = RunLog.open(self.root, day)
        snapshot = log.result(SNAPSHOT_STEP) if log.done(SNAPSHOT_STEP) else {}
        valid = bool(snapshot.get("valid"))
        marks = snapshot_marks(self.snapshots.snapshot(day, snapshot["snapshot_id"])) if valid else {}
        lines = [line for review in self.reviews for line in review.review(day, marks)]
        status, reason = (STEP_OK, "; ".join(lines)) if valid else (STEP_REFUSED, UNMARKED)
        result = {"status": status, "reason": reason, "lines": lines, "marked_contracts": len(marks)}
        return StepOutcome({"snapshot_id": snapshot.get("snapshot_id")}, result, tuple(self.changed(self.pathspecs)))
