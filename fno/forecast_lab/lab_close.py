"""`lab close` (story FL1-1): the 15:45 report, written once and posted once to #fno-forecast. A rerun after the
report was written posts the stored text and alerts, never rebuilt ones (scores may have moved since). A rerun after
the post posts nothing. Each missing or late forecast is one alert to #fno-desk, and so is a report not posted. A post
Slack may have made without answering is never retried (no double post); the alert says to check the channel."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import date, datetime

from ..alerts.sender import AlertSender
from ..cards.posting import CardPoster
from ..quotes.recorder import RECORDED_SESSION_KINDS
from .constants import (
    ALERT,
    ALREADY_POSTED,
    HEADER,
    ISSUE_CLOSE,
    MAY_HAVE_POSTED,
    NOT_A_SESSION,
    NOT_POSTED,
    POSTED,
    UNDERLYINGS,
)
from .match import MatchSection, next_ranges
from .ranges import RangeForecasts
from .scoreboard import scoreboard_lines, trust_line


class ReportRecords(ABC):
    """The report's write-once records (O9: Drive data area, one receipt each)."""

    @abstractmethod
    def report(self, day: date) -> tuple[str, list[str]] | None:
        """The day's report text and its alerts as written, or None."""

    @abstractmethod
    def write_report(self, day: date, text: str, alerts: list[str]) -> None: ...

    @abstractmethod
    def posted(self, day: date) -> bool: ...

    @abstractmethod
    def mark_posted(self, day: date, outcome: str) -> None: ...


class Sections(ABC):
    """More report lines (FL1-1's contract tracking joins here), each section with its alerts."""

    @abstractmethod
    def lines(self, day: date) -> tuple[list[str], list[str]]: ...


class CloseReport:
    def __init__(self, forecasts: RangeForecasts, match: MatchSection, extra: tuple[Sections, ...] = (),
                 underlyings: tuple[str, ...] = UNDERLYINGS):  # fmt: skip
        self.forecasts, self.match, self.extra, self.underlyings = forecasts, match, extra, underlyings

    def build(self, day: date, now: datetime) -> tuple[str, list[str]]:
        lines, alerts = [HEADER.format(day=day)], []
        for underlying in self.underlyings:
            matched, missed = self.match.lines(underlying, day)
            lines += ["", *matched]
            alerts += missed
        for underlying in self.underlyings:
            lines += ["", *next_ranges(underlying, self.forecasts.sealed(underlying, day, ISSUE_CLOSE), now)]
        for underlying in self.underlyings:
            lines += ["", f"{underlying}:", *scoreboard_lines(self.forecasts.history(underlying, day))]
        for section in self.extra:
            more, more_alerts = section.lines(day)
            lines += ["", *more]
            alerts += more_alerts
        lines += ["", trust_line(self.forecasts, self.underlyings, day)]
        return "\n".join(lines) + "\n", alerts


class LabClose:
    def __init__(self, report: CloseReport, records: ReportRecords, poster: CardPoster, desk: AlertSender,
                 session_kind: Callable[[date], str | None], clock: Callable[[], datetime]):  # fmt: skip
        self.report, self.records, self.poster, self.desk = report, records, poster, desk
        self.session_kind, self.clock = session_kind, clock

    def run(self, day: date) -> list[str]:
        if self.session_kind(day) not in RECORDED_SESSION_KINDS:
            return [NOT_A_SESSION.format(day=day)]
        if self.records.posted(day):
            return [ALREADY_POSTED.format(day=day)]
        written = self.records.report(day)
        if written is None:
            written = self.report.build(day, self.clock())
            self.records.write_report(day, *written)
        text, alerts = written
        receipt = self.poster.post(text)
        if receipt.sent or MAY_HAVE_POSTED in receipt.outcome:
            self.records.mark_posted(day, receipt.outcome)
        if not receipt.sent:
            alerts = [*alerts, NOT_POSTED.format(outcome=receipt.outcome)]
        sent = [self.desk.send(ALERT.format(day=day, what=what)) for what in alerts]
        return [POSTED.format(day=day, outcome=receipt.outcome, alerts=len(sent))]
