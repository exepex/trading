"""One mark's alerts (story LM1, design 6.5): the limits decide what is sent, every condition found is recorded, and
the order keeps a crash visible: the `sending` rows are written first, then each alert is sent, then the outcomes.
If Drive is down the alerts still go out (the owner's warning matters more than its record; reasoning only) and the
result says the record failed. A send Slack refused is `failed`: it is not in the history, so the next mark sends it
again while the condition lasts, and this mark's record keeps the first try."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from ..alerts.sender import SENT as SLACK_SENT
from ..alerts.sender import AlertSender
from .alert_records import FAILED, HELD, SENDING, SENT, AlertRecords, AlertRecordsUnavailable, AlertRow
from .limits import AlertLimits
from .model import Condition, MarkFindings
from .settings import MonitorSettings
from .texts import alert_text


@dataclass(frozen=True)
class AlertOutcome:
    sent: int = 0
    failed: int = 0
    held: int = 0
    record_failed: bool = False
    lines: tuple[str, ...] = ()  # each send's outcome, as the sender reports it


class MonitorAlerting:
    def __init__(self, limits: AlertLimits, records: AlertRecords, alerts: AlertSender, settings: MonitorSettings,
                 clock: Callable[[], datetime]):  # fmt: skip
        self.limits, self.records, self.alerts, self.settings, self.clock = limits, records, alerts, settings, clock

    def handle(self, findings: MarkFindings) -> AlertOutcome:
        if not findings.conditions:
            return AlertOutcome()
        mark = findings.mark
        record_failed = False
        try:
            history = self.records.history(mark.session, mark.mark)
        except AlertRecordsUnavailable:
            history, record_failed = [], True
        decision = self.limits.decide(list(findings.conditions), history, mark.mark)
        due = [*decision.send, *([decision.summary] if decision.summary else [])]
        rows = [self._row(c, findings, HELD) for c in decision.held] + [self._row(c, findings, SENDING) for c in due]
        record_failed = not self._write(findings, rows) or record_failed
        lines = []
        for row in (r for r in rows if r.state == SENDING):
            outcome = self.alerts.send(row.text)
            row.state, row.sent_at, row.outcome = (SENT if outcome == SLACK_SENT else FAILED), self.clock(), outcome
            lines.append(outcome)
        record_failed = not self._write(findings, rows) or record_failed
        sent = sum(r.state == SENT for r in rows)
        failed = sum(r.state == FAILED for r in rows)
        return AlertOutcome(sent, failed, len(decision.held), record_failed, tuple(lines))

    def _row(self, condition: Condition, findings: MarkFindings, state: str) -> AlertRow:
        mark = findings.mark
        return AlertRow(mark.session, mark.mark, condition.check, condition.severity, condition.key,
                        condition.trade_id, state, self.settings.version, alert_text(condition, mark, self.settings),
                        mark.clock_skew_seconds)  # fmt: skip

    def _write(self, findings: MarkFindings, rows: list[AlertRow]) -> bool:
        try:
            self.records.write(findings.mark.session, findings.mark.mark, rows)
        except AlertRecordsUnavailable:
            return False
        return True
