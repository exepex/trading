"""The monitor's alert records (story LM1): one private file per mark, `journal/monitor/alerts/<YYYY>/<YYYY-MM-DD>/
<HHMM>.csv`, in Drive's `paper` area beside E2c's private paper records (a record names a position and its loss, so it
is never committed; the local copy is git-ignored). One file per mark means one writer per file, so overlapping runs
never overwrite each other's rows (Drive's `replace` has no append).

A row is one condition on the mark: `held` (inside a limit, recorded, not sent), `sending` (written before the send, so
a crash in between stays visible), then `sent` or `failed`. The session's history, read back for the alert limits, is
the rows that were sent."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from ..intraday.document import parse_time, utc_text
from ..intraday.slots import marks
from ..models import IST
from ..storage.index_store import IndexFileStore
from .limits import SentAlert

ALERTS_FOLDER = "journal/monitor/alerts"
FILE_NAME = "{day:%Y}/{day:%Y-%m-%d}/{mark:%H%M}.csv"
HELD, SENDING, SENT, FAILED = "held", "sending", "sent", "failed"
COLUMNS = ("session", "mark", "check", "severity", "key", "trade_id", "state", "sent_at", "outcome", "version",
           "clock_skew_seconds", "text")  # fmt: skip
UNAVAILABLE = "monitor alert records in Drive could not be {what} ({path}: {why})"


class AlertRecordsUnavailable(RuntimeError):
    """Drive could not be read or written: the alert is still sent, the mark row says the record failed."""


@dataclass
class AlertRow:
    session: date
    mark: datetime
    check: str
    severity: str
    key: str
    trade_id: str
    state: str
    version: str
    text: str
    clock_skew_seconds: float | None = None
    sent_at: datetime | None = None
    outcome: str = ""

    def as_csv(self) -> dict[str, str]:
        skew = "" if self.clock_skew_seconds is None else repr(self.clock_skew_seconds)
        return {
            "session": self.session.isoformat(), "mark": utc_text(self.mark), "check": self.check,
            "severity": self.severity, "key": self.key, "trade_id": self.trade_id, "state": self.state,
            "sent_at": utc_text(self.sent_at), "outcome": self.outcome, "version": self.version,
            "clock_skew_seconds": skew, "text": self.text,
        }  # fmt: skip


class AlertRecords:
    def __init__(self, store: IndexFileStore, root: Path):
        self.store, self.root = store, Path(root)

    def name(self, day: date, mark: datetime) -> str:
        return f"{ALERTS_FOLDER}/{FILE_NAME.format(day=day, mark=mark.astimezone(IST))}"

    def write(self, day: date, mark: datetime, rows: list[AlertRow]) -> None:
        """The mark's whole file, locally and then in Drive (replacing this run's earlier version of it)."""
        name, data = self.name(day, mark), _to_bytes(rows)
        local = self.root / name
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(data)
        self._call("written", name, lambda: self.store.replace(name, data))

    def history(self, day: date, before: datetime) -> list[SentAlert]:
        """The alerts sent on the session's earlier marks. A mark this host wrote is read from its local copy (one
        writer per mark file, so the copy is the record); any other mark from Drive, where every run's records are.
        That keeps a mark's Drive reads to the marks other runs handled (A16's per-member time limit)."""
        sent = []
        for mark in (m for m in marks(day) if m < before):
            data = self._read(self.name(day, mark))
            rows = csv.DictReader(io.StringIO(data.decode("utf-8"))) if data else []
            sent += [SentAlert(r["key"], r["severity"], parse_time(r["mark"])) for r in rows if r["state"] == SENT]
        return sent

    def _read(self, name: str) -> bytes | None:
        local = self.root / name
        if local.is_file():
            return local.read_bytes()
        return self._call("read", name, lambda: self.store.get(name))

    @staticmethod
    def _call(what: str, name: str, action):
        try:
            return action()
        except Exception as problem:  # noqa: BLE001 - any Drive failure is this record's, named by class only
            raise AlertRecordsUnavailable(
                UNAVAILABLE.format(what=what, path=name, why=type(problem).__name__)
            ) from problem


def _to_bytes(rows: list[AlertRow]) -> bytes:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(r.as_csv() for r in rows)
    return out.getvalue().encode("utf-8")
