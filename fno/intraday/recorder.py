"""Takes the 15-minute snapshots of a session (story A16) and keeps the books on them: raw document to the store,
one ledger row per due mark (a mark nobody took becomes `missed`, never filled), the alert after two bad marks in a
row, the heartbeat, the session's realised variance once its last mark is settled, and the commit of the repository
files. Knows no broker: the source, store, clock servers, alerts and publisher are interfaces.

Which day is a session comes only from NSE's calendar (A7): regular and special sessions are recorded, a muhurat-only
day is not (as A4); a day outside the calendar raises `CalendarError` (the command stops loudly)."""

from __future__ import annotations

import time as clock
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, time

from ..alerts.sender import AlertSender
from ..constants import SESSION_MUHURAT
from ..models import IST, now_ist
from ..quotes.recorder import MUHURAT_ONLY, RECORDED_SESSION_KINDS
from ..research_data.calendar import SessionCalendar
from ..storage.manifest_commit import ManifestRecorder
from ..storage.raw_store import RawFileStore
from .clock import ClockCheck
from .document import utc_text
from .heartbeat import Heartbeat
from .ledger import SlotLedger
from .session_rv import SessionRv
from .settle import Settlement
from .slots import label, marks, takeable_marks, window_end
from .source import IntradayQuoteSource

NOT_TRADING_DAY, ALREADY, NO_MARK, MISSED_NOW = "not a trading day", "already recorded", "no mark now", "missed"
NO_MARK_DETAIL = "no mark open or due within 15 minutes"
LATE_START = "the mark's 120 s window closed before the index request could go out"
TAKEN_DETAIL = (
    "{recorded_contracts} of {expected_contracts} contracts ({two_sided_contracts} two-sided), index answered "
    "{lateness_seconds} s after the mark; failures: {failures}"
)
GOOD_OUTCOMES = ("good", ALREADY, NOT_TRADING_DAY, NO_MARK)


@dataclass
class SlotOutcome:
    status: str
    mark: str = ""
    detail: str = ""
    lines: list[str] = field(default_factory=list)  # alert outcomes, clock warning, realised variance, commit

    def summary(self) -> str:
        head = f"{self.mark} {self.status}" if self.mark else self.status
        return f"{head}: {self.detail}" if self.detail else head


class IntradayRecorder:
    def __init__(self, source: IntradayQuoteSource, store: RawFileStore, ledger: SlotLedger, heartbeat: Heartbeat,
                 calendar: SessionCalendar, alerts: AlertSender, clock_check: ClockCheck, session_rv: SessionRv,
                 publisher: ManifestRecorder, now: Callable[[], datetime] = now_ist, sleep=clock.sleep):  # fmt: skip
        self.source, self.store, self.ledger, self.heartbeat = source, store, ledger, heartbeat
        self.calendar, self.alerts, self.clock_check, self.session_rv = calendar, alerts, clock_check, session_rv
        self.publisher, self.now, self.sleep = publisher, now, sleep
        self.settlement = Settlement(source.name, store, ledger, alerts)

    def snapshot(self, until: time | None = None) -> SlotOutcome:
        """Takes the next open or coming mark (waiting at most 15 minutes), unless it is after `until`."""
        started = self.now()
        day = started.astimezone(IST).date()
        kind = self.calendar.session_kind(day)
        if kind not in RECORDED_SESSION_KINDS:
            return SlotOutcome(NOT_TRADING_DAY, detail=MUHURAT_ONLY if kind == SESSION_MUHURAT else "")
        open_marks = [m for m in takeable_marks(day, started) if until is None or m.time() <= until]
        mark = next((m for m in open_marks if not self._stored(day, m)), None)
        if mark is None:
            status, detail = (ALREADY, "") if open_marks else (NO_MARK, NO_MARK_DETAIL)
            return self._close(day, started, SlotOutcome(status, label(open_marks[0]) if open_marks else "", detail))
        self.source.prepare(day)
        wait = (mark - self.now()).total_seconds()
        if wait > 0:
            self.sleep(wait)
        if self.now() > window_end(mark):
            return self._close(day, started, SlotOutcome(MISSED_NOW, label(mark), LATE_START))
        doc = self.source.take(day, mark)
        data = doc.to_bytes()
        self.store.put(self.settlement.path(day, mark), data)
        reading = self.clock_check.check()
        outcome = SlotOutcome("", label(mark), lines=[reading.warning()] if reading.warning() else [])
        return self._close(day, started, outcome, (doc, data, reading))

    def run(self, until: time) -> list[SlotOutcome]:
        """The session loop: every mark up to `until` (IST), each waited for; stops on a day not recorded."""
        outcomes = []
        while self.now().astimezone(IST).time() < until:
            outcome = self.snapshot(until)
            outcomes.append(outcome)
            if outcome.status in (NOT_TRADING_DAY, NO_MARK, ALREADY):  # nothing left to take now
                break
        return outcomes

    def settle_day(self, day: date) -> list[str]:
        """Writes the missed rows of a past or finished session and its realised variance (the `rv` command)."""
        rows, alert = self.settlement.settle(day, self.now(), None)
        lines = [alert] if alert else []
        return lines + self._finish_session(day) + [self.publisher.commit(f"{day} settled ({len(rows)} rows)")]

    def _stored(self, day: date, mark: datetime) -> bool:
        return self.store.get(self.settlement.path(day, mark)) is not None

    def _close(self, day: date, started: datetime, outcome: SlotOutcome, taken=None) -> SlotOutcome:
        """Settles the ledger, alerts, heartbeat, realised variance once the session is complete, and the commit."""
        rows, alert = self.settlement.settle(day, self.now(), taken)
        outcome.lines += [alert] if alert else []
        mine = next((r for r in rows if r["mark_ist"] == outcome.mark), None)
        if taken is not None and mine is not None:
            outcome.status, outcome.detail = mine["status"], TAKEN_DETAIL.format(**mine)
        if len(self.ledger.rows(day)) == len(marks(day)):
            outcome.lines += self._finish_session(day)
        self.heartbeat.write({
            "recorder": "story A16 intraday recorder", "session": day.isoformat(), "mark": outcome.mark,
            "status": outcome.status, "run_started_at": utc_text(started), "run_finished_at": utc_text(self.now()),
            "clock_status": taken[2].status if taken else "", "clock_skew_seconds": taken[2].worst if taken else None,
        })  # fmt: skip
        outcome.lines.append(self.publisher.commit(f"{day} {outcome.mark or outcome.status}"))
        return outcome

    def _finish_session(self, day: date) -> list[str]:
        return [self.session_rv.compute(day), self.session_rv.void_share_line()]
