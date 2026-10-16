"""The position monitor (story LM1): one mark in, what it found out. Staleness first: a mark the monitor cannot use
(A16's status outside the usable ones, or no index level) is "no check" and only the stale-quotes check runs on it.
With no open position nothing runs and nothing is found (a monitor with nothing to watch adds nothing)."""

from __future__ import annotations

from ..intraday.slots import marks
from .checks import MonitorCheck, QuotesStale
from .model import MarkFindings, MonitorMark, WatchedPosition
from .settings import MonitorSettings


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
            found += [c for check in self.checks for c in check.find(mark, positions)]
        return MarkFindings(mark, len(positions), tuple(found))
