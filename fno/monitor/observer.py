"""The position monitor behind A16's mark observer port (story LM1): A16's recorder calls it once per newly settled
mark. It never opens, changes or closes a trade.

Per mark: a mark that already has its public row is never handled again; with no open position nothing is checked or
sent; otherwise the checks run (staleness first), the alerts go out under their limits with their private record, and
the public row and the heartbeat are written last. A failure is named in the row and the heartbeat by class only, then
raised, so A16's recorder names it too and carries on."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime

from ..intraday.document import SnapshotDocument
from ..intraday.observer import MarkObserver
from .alerting import AlertOutcome, MonitorAlerting
from .heartbeat import MonitorHeartbeat
from .mark_reader import MarkReader
from .mark_rows import RECORD_FAILED, RECORD_NONE, RECORD_OK, MarkRow, MarkRows
from .monitor import PositionMonitor
from .positions import OpenPositionSource


class MonitorObserver(MarkObserver):
    def __init__(self, positions: OpenPositionSource, reader: MarkReader, monitor: PositionMonitor,
                 alerting: MonitorAlerting, rows: MarkRows, heartbeat: MonitorHeartbeat,
                 clock: Callable[[], datetime], out: Callable[[str], None] = print):  # fmt: skip
        self.positions, self.reader, self.monitor, self.alerting = positions, reader, monitor, alerting
        self.rows, self.heartbeat, self.clock, self.out = rows, heartbeat, clock, out

    def after_mark(self, day: date, mark: datetime, document: SnapshotDocument | None, status: str) -> None:
        if self.rows.handled(day, mark):
            return
        try:
            row = self._handle(day, mark, document, status)
        except Exception as error:
            self._finish(MarkRow(day, mark, self.clock(), status, False, 0, failure=type(error).__name__))
            raise
        self._finish(row)

    def _handle(self, day, mark, document, status) -> MarkRow:
        positions = self.positions.positions(day, mark, document)
        if not positions:
            return MarkRow(day, mark, self.clock(), status, False, 0)
        read = self.reader.read(day, mark, document, status)
        outcome = self.alerting.handle(self.monitor.find(read, positions))
        for line in outcome.lines:
            self.out(line)  # an "alert NOT sent" line is posted with the Slack connector (CLAUDE.md)
        return MarkRow(day, mark, self.clock(), status, self.monitor.usable(read), len(positions), outcome.sent,
                       outcome.failed, outcome.held, _record(outcome), read.previous_close is not None)  # fmt: skip

    def _finish(self, row: MarkRow) -> None:
        self.rows.append(row)
        self.heartbeat.beat(row)


def _record(outcome: AlertOutcome) -> str:
    if outcome.record_failed:
        return RECORD_FAILED
    return RECORD_OK if outcome.sent or outcome.failed or outcome.held else RECORD_NONE
