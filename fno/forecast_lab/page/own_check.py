"""An edition's own check of one forecast, before G13b scores it (story FL1-1d): the previous session's next-session
forecast (by the page's method), against a close.
- The evening checks today's forecast on today's close as read from NSE's index list (A4h), labelled provisional
  until the official file confirms it the next morning.
- The morning checks the previous session's forecast on NSE's official close, when no score of it exists yet (G13b
  scores it in the 14:33 run): a day the evening could not check still gets its result the next morning
  (orchestrator, 22 Oct)."""

from __future__ import annotations

from collections.abc import Collection
from datetime import date

from ..constants import ISSUE_CLOSE
from ..ranges import Outcomes, RangeSource, TodayCloses
from ..sessions import RegularSessions
from .model import Band, Outcome

NOT_READ = (
    "today's close was not read ({why}); today is not checked here, and its result appears in tomorrow morning's "
    "report once NSE's official close is archived"
)


def band_of(row) -> Band:
    q = row.quantiles
    return Band(q[0.05], q[0.25], q[0.50], q[0.75], q[0.95])


class OwnCheck:
    def __init__(self, ranges: RangeSource, sessions: RegularSessions, today_closes: TodayCloses,
                 official: Outcomes | None):  # fmt: skip
        self.ranges, self.sessions, self.today_closes, self.official = ranges, sessions, today_closes, official

    def _forecast(self, underlying: str, target: date, method: str):
        """(the issue, its next-session row by `method`) aimed at `target`, or (None, None)."""
        issue = self.ranges.sealed(underlying, self.sessions.previous(target), ISSUE_CLOSE)
        row = issue.row(method, "N1") if issue else None
        if row is None or row.target_day != target or row.status != "ok":
            return None, None
        return issue, row

    @staticmethod
    def _outcome(target: date, close: float, issue, row, provisional: bool) -> Outcome:
        band = band_of(row)
        return Outcome(target, close, band, band.q25 <= close <= band.q75, band.q05 <= close <= band.q95,
                       issue.sealed_at is not None and not issue.late, provisional=provisional)  # fmt: skip

    def evening(self, underlying: str, day: date, method: str) -> tuple[Outcome | None, str | None]:
        """(today's check on today's close as read, or None; why no close was read, or None)."""
        issue, row = self._forecast(underlying, day, method)
        if row is None:
            return None, None
        close = self.today_closes.close(underlying, day)
        if close is None:
            return None, NOT_READ.format(why=self.today_closes.why_missing(day))
        return self._outcome(day, close, issue, row, provisional=True), None

    def morning(self, underlying: str, day: date, method: str, scored: Collection[date]) -> Outcome | None:
        """The previous session's check on its official close, unless G13b has scored it already."""
        previous = self.sessions.previous(day)
        if previous in scored or self.official is None:
            return None
        issue, row = self._forecast(underlying, previous, method)
        close = self.official.close(underlying, previous) if row is not None else None
        return None if close is None else self._outcome(previous, close, issue, row, provisional=False)
