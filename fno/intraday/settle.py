"""Brings a session's ledger up to date (story A16): a row for the snapshot just taken, a row for every stored
snapshot that has none yet (a run that stopped after saving), and a `missed` row for every due mark with no snapshot.
Then the streak alert: its outcome line is kept in the newest row."""

from __future__ import annotations

import hashlib
from datetime import date, datetime

from ..alerts.sender import AlertSender
from ..storage.raw_store import RawFileStore
from .document import SnapshotDocument, snapshot_path, utc_text
from .ledger import SlotLedger, missed_row, taken_row
from .slots import marks, window_end
from .status import verdict
from .streak import streak_alert_text

ALERT_LINE = "ALERT: {text} -> {outcome}"


class Settlement:
    def __init__(self, source: str, store: RawFileStore, ledger: SlotLedger, alerts: AlertSender):
        self.source, self.store, self.ledger, self.alerts = source, store, ledger, alerts

    def path(self, day: date, mark: datetime) -> str:
        return snapshot_path(self.source, day, mark)

    def settle(self, day: date, now: datetime, taken=None) -> tuple[list[dict], str]:
        """The rows written now, and the alert line ("" when no alert was due). `taken`: (document, bytes, clock
        reading) of the snapshot just taken, or None."""
        existing = self.ledger.rows(day)
        have = {row["mark"] for row in existing}
        new = []
        for mark in marks(day):
            if utc_text(mark) in have:
                continue
            if taken is not None and taken[0].mark == mark:
                new.append(self._row(day, mark, *taken))
            elif window_end(mark) < now:
                data = self.store.get(self.path(day, mark))
                document = SnapshotDocument.from_bytes(data) if data else None
                new.append(self._row(day, mark, document, data, None) if document else missed_row(
                    day, mark, self.source, now))  # fmt: skip
        lines = [line for position in range(len(new)) if (line := self._alert(existing + new[: position + 1], now))]
        self.ledger.append(day, new)
        return new, "\n".join(lines)

    def _row(self, day: date, mark: datetime, document: SnapshotDocument, data: bytes, reading) -> dict:
        judged = verdict(document, self._previous_level(day, mark))
        return taken_row(document, judged, self.path(day, mark), hashlib.sha256(data).hexdigest(), reading)

    def _previous_level(self, day: date, mark: datetime) -> float | None:
        session_marks = marks(day)
        position = session_marks.index(mark)
        if position == 0:
            return None
        data = self.store.get(self.path(day, session_marks[position - 1]))
        return SnapshotDocument.from_bytes(data).index_level if data else None

    def _alert(self, rows: list[dict], now: datetime) -> str:
        """The streak alert as of the newest row, kept in that row (rows are settled in mark order, so a streak
        followed by a good mark in the same settlement is still alerted)."""
        text = streak_alert_text(rows, now)
        if not text:
            return ""
        rows[-1]["alert"] = ALERT_LINE.format(text=text, outcome=self.alerts.send(text))
        return rows[-1]["alert"]
