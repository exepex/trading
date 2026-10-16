"""The position monitor (story LM1): one mark in, what it found out. Staleness first: a mark the monitor cannot use
(A16's status outside the usable ones, or no index level) is "no check" and only the stale-quotes check runs on it.
With no open position nothing runs and nothing is found (a monitor with nothing to watch adds nothing). A check that
fails is a WARNING of its own, and the other checks still run (judge 264)."""

from __future__ import annotations

from ..intraday.slots import marks
from .checks import MonitorCheck, QuotesStale
from .model import DESK, HOURLY, WARNING, Condition, MarkFindings, MonitorMark, WatchedPosition
from .settings import MonitorSettings

CHECK_FAILED_NAME = "check_failed"
CHECK_FAILED = "the {check} check could not run on this mark ({error}); the other checks ran"


class PositionMonitor:
    def __init__(self, settings: MonitorSettings, checks: list[MonitorCheck], stale: QuotesStale):
        self.settings, self.checks, self.stale = settings, checks, stale

    def usable(self, mark: MonitorMark) -> bool:
        return mark.status in self.settings.usable_statuses and mark.index_level is not None

    def find(self, mark: MonitorMark, positions: list[WatchedPosition]) -> MarkFindings:
        if not positions:
            return MarkFindings(mark, 0)
        found = list(self.stale.find(mark, marks(mark.session)[0]))
        if self.usable(mark):
            found += [c for check in self.checks for c in self._run(check, mark, positions)]
        return MarkFindings(mark, len(positions), tuple(found))

    @staticmethod
    def _run(check: MonitorCheck, mark: MonitorMark, positions: list[WatchedPosition]) -> list[Condition]:
        """One check's failure is its own WARNING, named by class only; it never takes the other checks down."""
        try:
            return check.find(mark, positions)
        except Exception as error:  # noqa: BLE001 - any failure of one check, reported, never silent
            facts = CHECK_FAILED.format(check=check.name, error=type(error).__name__)
            return [Condition(CHECK_FAILED_NAME, WARNING, DESK, f"{CHECK_FAILED_NAME}:{check.name}", HOURLY, facts)]
