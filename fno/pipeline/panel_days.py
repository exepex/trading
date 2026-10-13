"""The daily NIFTY panel job (story A13; G1 protocol v3 proposal, response 68): after NSE's evening F&O file, each
session after the panel's last day is built with A3's own builder (unchanged rules) from the files archived in Drive
(A11: the newest version held at the run) and appended in place (`PanelAppender`), never rewriting a day.

It writes only under a frozen protocol: the injected freeze check runs first, and before version 3 is frozen nothing
is appended. A built day's NIFTY 50 and India VIX closes must equal that day's row in the warm-up closes (story O6
appends them first), so one day never has two closes. It stops at the first session that fails, keeps the sessions
before it, and posts one line.
"""

from __future__ import annotations

import csv
from collections.abc import Callable
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from ..alerts.sender import AlertSender
from ..forecast.freeze import NotFrozen
from ..forecast.freeze_v2 import NotYetFrozen
from ..research_data.calendar import SessionCalendar
from ..research_data.nifty_panel import NiftyPanelBuilder, PanelBuildError
from ..research_data.panel_append import AppendRefused, PanelAppender
from ..research_data.panel_rows import OPTION_COLUMNS, OPTIONS
from ..research_data.panel_store import WARMUP_FILE, PanelDay

ADDED = "panel days: {added} sessions appended ({first} to {last})"
NOTHING_NEW = "panel days: nothing new after {last}"
WAITING = "panel days: nothing appended: {reason}"
STOPPED = (
    "Omenix F&O daily NIFTY panel: stopped at {day}: {problem}; {added} earlier sessions appended. The next run retries"
)
REFUSED = "Omenix F&O daily NIFTY panel: nothing appended: {problem}"
UNDERLYING, VIX = OPTION_COLUMNS.index("underlying"), OPTION_COLUMNS.index("vix")


def warmup_closes(folder: Path) -> dict[str, tuple[Decimal, Decimal]]:
    """The official closes O6 appended (`warmup_closes.csv`), by ISO date."""
    path = Path(folder) / WARMUP_FILE
    if not path.is_file():
        return {}
    rows = csv.DictReader(path.read_text(encoding="utf-8").splitlines())
    return {r["date"]: (Decimal(r["underlying"]), Decimal(r["vix"])) for r in rows}


def closes_problem(panel_day: PanelDay, closes: dict[str, tuple[Decimal, Decimal]]) -> str | None:
    """Why the day's closes disagree with the warm-up closes (None when they agree or the day has no rows)."""
    rows = panel_day.rows.get(OPTIONS)
    if not rows:
        return None
    day = panel_day.day.isoformat()
    if day not in closes:
        return f"no {WARMUP_FILE} row for {day} yet (the daily index-close job appends it first)"
    built = (Decimal(rows[0][UNDERLYING]), Decimal(rows[0][VIX]))
    return None if built == closes[day] else f"closes {built} differ from {WARMUP_FILE}'s {closes[day]}"


class PanelDayJob:
    def __init__(
        self,
        builder: NiftyPanelBuilder,
        appender: PanelAppender,
        calendar: SessionCalendar,
        freeze_check: Callable[[], object],
        alerts: AlertSender,
        clock: Callable[[], datetime],
        log: Callable[[str], None] = print,
    ):
        self.builder, self.appender, self.calendar = builder, appender, calendar
        self.freeze_check, self.alerts, self.clock, self.log = freeze_check, alerts, clock, log

    def run(self, today: date) -> int:
        try:
            self.freeze_check()
        except NotYetFrozen as waiting:
            self.log(WAITING.format(reason=waiting))
            return 0
        except NotFrozen as problem:
            return self._fail(REFUSED.format(problem=f"protocol freeze check failed: {problem}"))
        try:
            return self._append(today)
        except AppendRefused as problem:
            return self._fail(REFUSED.format(problem=problem))

    def _append(self, today: date) -> int:
        last = self.appender.last_day()
        days, stop = self._built_days(last, today)
        stamp = {"appended_at": self.clock().isoformat(), "calendar_sha256": self.calendar.calendar_sha256()}
        added = self.appender.append(days, stamp)
        if added:
            self.log(ADDED.format(added=added, first=days[0].day, last=days[-1].day))
        else:
            self.log(NOTHING_NEW.format(last=last))
        return 0 if stop is None else self._fail(STOPPED.format(day=stop[0], problem=stop[1], added=added))

    def _built_days(self, last: date, today: date) -> tuple[list[PanelDay], tuple[date, str] | None]:
        closes, days = warmup_closes(self.appender.folder), []
        for day in self.calendar.sessions(last + timedelta(days=1), today):
            try:
                (panel_day,) = list(self.builder.days(day, day))
            except PanelBuildError as error:
                return days, (day, "; ".join(error.problems))
            problem = closes_problem(panel_day, closes)
            if problem:
                return days, (day, problem)
            days.append(panel_day)
        return days, None

    def _fail(self, line: str) -> int:
        self.log(line)
        self.log(self.alerts.send(line))
        return 1
