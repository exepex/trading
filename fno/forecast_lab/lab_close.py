"""`lab close` (story FL1-1): the 15:45 report, written once, posted once to #fno-forecast, its alerts sent once to
#fno-desk. A rerun after the report was written posts the stored text and alerts, never rebuilt ones (scores may have
moved since). Each step has its own write-once marker (judge 422): a rerun after the post sends no second post, and a
rerun after the alerts sends no second alert. The alerts' marker is written after the sends (a crash in between sends
them again rather than losing them). Every alert's outcome is printed, an unsent one with its text so the routine
posts it by hand (CLAUDE.md, step 3). A report not posted is the step's failure: the command exits non-zero and O1's
`Alerted` alerts it once (O1's exit contract: a step never alerts its own failure). A post Slack may have made without
answering is never retried (no double post), so it is marked posted and the failure says to check the channel."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date, datetime

from ..alerts.sender import SENT, AlertSender
from .constants import (
    ALERT,
    ALERTS_ALREADY,
    ALERTS_SENT,
    ALREADY_POSTED,
    CHECK_BEFORE_REPOST,
    NOT_A_SESSION,
    NOT_POSTED,
    REPORT_ALREADY,
    REPORT_POSTED,
)
from .delivery import ReportPoster
from .maker import ReportMaker
from .report import CloseReport
from .written import WrittenReport


class ReportRecords(ABC):
    """The report's write-once records (O9: Drive data area, one receipt each)."""

    @abstractmethod
    def report(self, day: date) -> WrittenReport | None:
        """The day's report as written, or None."""

    @abstractmethod
    def write_report(self, day: date, report: WrittenReport) -> None: ...

    @abstractmethod
    def posted(self, day: date) -> bool: ...

    @abstractmethod
    def mark_posted(self, day: date, outcome: str) -> None: ...

    @abstractmethod
    def alerted(self, day: date) -> bool: ...

    @abstractmethod
    def mark_alerted(self, day: date, outcomes: list[str]) -> None: ...


@dataclass(frozen=True)
class LabResult:
    lines: list[str]
    failed: bool = False


class LabClose:
    def __init__(self, report: CloseReport, maker: ReportMaker, records: ReportRecords, poster: ReportPoster,
                 desk: AlertSender, is_regular: Callable[[date], bool], clock: Callable[[], datetime]):  # fmt: skip
        self.report, self.maker, self.records, self.poster, self.desk = report, maker, records, poster, desk
        self.is_regular, self.clock = is_regular, clock

    def run(self, day: date) -> LabResult:
        if not self.is_regular(day):
            return LabResult([NOT_A_SESSION.format(day=day)])
        posted, alerted = self.records.posted(day), self.records.alerted(day)
        if posted and alerted:
            return LabResult([ALREADY_POSTED.format(day=day)])
        written = self.records.report(day)
        if written is None:
            written = self._make(day)
            self.records.write_report(day, written)
        lines, failed = [REPORT_ALREADY.format(day=day)], False
        if not posted:
            lines, failed = self._post(day, written)
        lines += [ALERTS_ALREADY.format(day=day)] if alerted else self._alert(day, written)
        return LabResult(lines, failed)

    def _make(self, day: date) -> WrittenReport:
        """The seal checks and matches decide the alerts and what is covered (FL1-1); the maker the message (FL1-1c)."""
        now = self.clock()
        checked = self.report.build(day, now, self.records.report)
        text, files, extra = self.maker.make(day, now, checked.alerts, checked.text)
        return replace(checked, text=text, alerts=checked.alerts + tuple(extra), attachments=files)

    def _post(self, day: date, written: WrittenReport) -> tuple[list[str], bool]:
        delivery = self.poster.post(written.text, list(written.attachments))
        if delivery.sent or delivery.may_have_posted:
            self.records.mark_posted(day, delivery.outcome)
        line = REPORT_POSTED.format(day=day, outcome="posted" if delivery.sent else delivery.outcome)
        if delivery.sent:
            return [line], False
        tail = CHECK_BEFORE_REPOST if delivery.may_have_posted else ""
        return [line, NOT_POSTED.format(outcome=delivery.outcome) + tail], True

    def _alert(self, day: date, written: WrittenReport) -> list[str]:
        texts = [ALERT.format(day=day, what=what) for what in written.alerts]
        outcomes = [self.desk.send(text) for text in texts]
        self.records.mark_alerted(day, outcomes)
        unsent = [f"{outcome}: {text}" for outcome, text in zip(outcomes, texts, strict=True) if outcome != SENT]
        return [ALERTS_SENT.format(day=day, sent=len(texts) - len(unsent), total=len(texts)), *unsent]
