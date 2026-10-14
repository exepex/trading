"""Where the live-feature gate (B7) gets each live feature's validation report. The committed reports are written by
`python -m fno research validate-live`; `RecomputedLiveReports` closes judge 44's follow-up: a committed report is used
only if every per-day value in it equals the value recomputed from the recorded data, so a hand-edited report fails."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from pathlib import Path

from ..research_engine.live_gate import reports_from_folder


class LiveReports(ABC):
    @abstractmethod
    def report(self, live_feature: str) -> Mapping | None:
        """The feature's validation report (B7 summary with per-day `comparisons`), or None if there is none."""


class CommittedLiveReports(LiveReports):
    def __init__(self, folder: Path):
        self.folder = folder

    def report(self, live_feature: str) -> Mapping | None:
        return reports_from_folder(self.folder).get(live_feature)


class RecomputedLiveReports(LiveReports):
    """The committed report, only when its per-day rows match a fresh recomputation of the same days."""

    def __init__(self, committed: LiveReports, recompute: Callable[[str], Mapping]):
        self.committed, self.recompute = committed, recompute

    def report(self, live_feature: str) -> Mapping | None:
        report = self.committed.report(live_feature)
        if report is None:
            return None
        fresh = {row["day"]: row for row in self.recompute(live_feature)["comparisons"]}
        return report if all(fresh.get(row["day"]) == row for row in report["comparisons"]) else None
