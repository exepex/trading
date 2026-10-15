"""The candle back-fill (story A16b): Groww's 15-minute windows of up to 90 days, each session's 1-minute check, NSE's
day and one row per recorded session, in calendar order.

- Raw first: each answer is archived in Drive with its manifest row before any row is derived from it.
- Transient (a call or read failed: Groww, Drive or NSE) defers the session: no row, named, exit 1, retried next run.
  Permanent (an answer received, the data absent) writes a void row (`session_deriver.py`).
- A session is written only when its previous recorded session has a row (else it is deferred), so a failed window
  never fixes a wrong overnight figure in place.
- Three Groww failures in a row stop the run rather than press a refusing service.
- Read-only towards Groww; never touches A16's files."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from ..quotes.recorder import RECORDED_SESSION_KINDS
from ..research_data.calendar import SessionCalendar
from ..storage.raw_store import RawFileConflict, StoredCopyDamaged
from .candle_archive import ArchivedCopy, CandleArchive, CopyDamaged
from .candle_levels import CANDLES_PER_SESSION, CandleParse, parse_candles
from .candle_rv_table import CandleRvTable
from .candle_source import FIFTEEN_MINUTES, CandleCallFailed, IntradayCandleSource
from .deferral_log import DeferralLog
from .nse_days import NseIndexDays, NseReadFailed
from .session_deriver import SessionDeriver, SessionInputs
from .session_rv import previous_recorded_session

SERIES_START = date(2020, 1, 1)  # Groww's 15-minute index history starts here (step 0)
WINDOW_DAYS = 90
FAILURES_TO_STOP = 3
STORE_FAILURES = (RawFileConflict, StoredCopyDamaged, CopyDamaged, OSError, RuntimeError)
NO_PREVIOUS_ROW = "previous session {day} has no row"


class BackfillStopped(RuntimeError):
    """Groww failed several times in a row: the run stopped; what it wrote stays."""


@dataclass
class BackfillReport:
    sessions: list[date] = field(default_factory=list)
    written: dict[date, dict] = field(default_factory=dict)
    held: int = 0  # sessions that already had a row
    deferred: dict[date, str] = field(default_factory=dict)
    windows: list[str] = field(default_factory=list)
    stopped: str = ""

    @property
    def complete(self) -> bool:
        return not self.deferred and not self.stopped


class CandleBackfill:
    def __init__(
        self,
        source: IntradayCandleSource,
        archive: CandleArchive,
        nse: NseIndexDays,
        table: CandleRvTable,
        deferrals: DeferralLog,
        deriver: SessionDeriver,
        calendar: SessionCalendar,
        clock: Callable[[], datetime],
        series_start: date = SERIES_START,
    ):
        """`series_start`: the first day of the series (its first session has no previous close)."""
        self.source, self.archive, self.nse, self.table = source, archive, nse, table
        self.series_start = series_start
        self.deferrals, self.deriver, self.calendar, self.clock = deferrals, deriver, calendar, clock
        self._failures, self._first = 0, None

    def run(self, start: date, end: date) -> BackfillReport:
        report = BackfillReport(sessions=self.recorded_sessions(max(start, self.series_start), end))
        self._first = self.first_session()
        try:
            for window_start, window_end in windows(report.sessions):
                self._window(window_start, window_end, report)
        except BackfillStopped as stop:
            report.stopped = str(stop)
            for day in report.sessions:
                if day not in report.written and day not in report.deferred and self.table.row(day) is None:
                    report.deferred[day] = "not reached: the run stopped"
        self.deferrals.append(self.clock(), report.deferred)
        return report

    def first_session(self) -> date | None:
        return next(iter(self.recorded_sessions(self.series_start, self.series_start + timedelta(days=14))), None)

    def recorded_sessions(self, start: date, end: date) -> list[date]:
        return [
            d for d in self.calendar.sessions(start, end) if self.calendar.session_kind(d) in RECORDED_SESSION_KINDS
        ]

    def _window(self, start: date, end: date, report: BackfillReport) -> None:
        days = [d for d in report.sessions if start <= d <= end]
        todo = [d for d in days if self.table.row(d) is None]
        report.held += len(days) - len(todo)
        if not todo:
            report.windows.append(f"window {start}..{end}: {len(days)} sessions already derived, not fetched")
            return
        copy = self._fetch(lambda: self.source.window(start, end), f"window {start}..{end}", todo, report)
        if copy is None:
            return
        found = sum(len(self.deriver.candles(d, copy).used) for d in days)
        expected = CANDLES_PER_SESSION * len(days)
        report.windows.append(f"window {start}..{end}: {found} of {expected} session candles ({len(days)} sessions)")
        for day in todo:
            self._session(day, copy, report)

    def _session(self, day: date, window: ArchivedCopy, report: BackfillReport) -> None:
        previous_close, why = self._previous_close(day, report)
        if why:
            report.deferred[day] = why
            return
        minutes = None
        if not self.deriver.candles(day, window).missing:
            minutes = self._fetch(lambda: self.source.minutes(day), f"1-minute {day}", [day], report)
            if minutes is None:
                return
        try:
            nse = self.nse.read(day)
        except NseReadFailed as failed:
            report.deferred[day] = str(failed)
            return
        row = self.deriver.derive(SessionInputs(day, window, minutes, nse, previous_close))
        self.table.write_once(row)
        report.written[day] = row

    def _previous_close(self, day: date, report: BackfillReport) -> tuple[float | None, str]:
        """The previous session's 15:30 level (None at the series start or when untrusted), or why `day` must wait."""
        if day == self._first:  # the series' first session: no previous close, a void overnight part
            return None, ""
        previous = previous_recorded_session(self.calendar, day)
        row = report.written.get(previous) or self.table.row(previous)
        if row is None:
            return None, NO_PREVIOUS_ROW.format(day=previous)
        try:
            window = self.archive.first_copy(FIFTEEN_MINUTES, previous)
        except STORE_FAILURES as failed:
            return None, f"previous session {previous}: Drive read failed: {type(failed).__name__}"
        if window is None:
            return None, f"previous session {previous}: its 15-minute copy is not in the manifest"
        return self.deriver.last_level(row, window), ""

    def _fetch(self, call, what: str, days: list[date], report: BackfillReport) -> ArchivedCopy | None:
        """The answer archived, or None with every session of `days` deferred (transient)."""
        try:
            answer = call()
            self._failures = 0
            parse_candles(answer.rows)  # an unreadable answer is transient too, and is not archived (criterion 1)
            return self.archive.save(answer)
        except CandleCallFailed as failed:
            reason = str(failed)
            self._failures += 1
        except (*STORE_FAILURES, CandleParse) as failed:
            reason = f"{what}: {type(failed).__name__}"
        for day in days:
            report.deferred[day] = reason
        if self._failures >= FAILURES_TO_STOP:
            raise BackfillStopped(f"{FAILURES_TO_STOP} Groww failures in a row, the last: {reason}")
        return None


def windows(sessions: list[date]) -> list[tuple[date, date]]:
    """Consecutive windows of at most WINDOW_DAYS calendar days covering the sessions."""
    found, index = [], 0
    while index < len(sessions):
        start = sessions[index]
        end = start + timedelta(days=WINDOW_DAYS - 1)
        found.append((start, min(end, sessions[-1])))
        while index < len(sessions) and sessions[index] <= end:
            index += 1
    return found
