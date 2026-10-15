"""Computes a finished session's realised variance from the snapshots stored in Drive (story A16): each mark's index
level is judged by the same rule as when it was taken (`status.index_check`), the strategy computes the figure, and the
row is written once. Also reports the share of void sessions (design 5.2: above 5%, a new version is proposed)."""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Callable
from datetime import date, datetime

from ..models import now_ist
from ..quotes.recorder import RECORDED_SESSION_KINDS
from ..research_data.calendar import SessionCalendar
from ..storage.raw_store import RawFileStore
from .document import SnapshotDocument, snapshot_path, utc_text
from .realised_vol import IntradayRealisedVol, RvResult
from .rv_table import RvTable
from .slots import label, marks
from .status import index_check

VOID_SHARE_LIMIT = 0.05
OK, VOID = "ok", "void"
VOID_SHARE_LINE = "void sessions: {void} of {total} ({share:.1%}){flag}"
VOID_SHARE_FLAG = " - above 5%: propose a new version (design 5.2)"


class SessionRv:
    def __init__(self, store: RawFileStore, source: str, calendar: SessionCalendar, table: RvTable,
                 strategy: IntradayRealisedVol, now: Callable[[], datetime] = now_ist):  # fmt: skip
        self.store, self.source, self.calendar, self.table = store, source, calendar, table
        self.strategy, self.now = strategy, now

    def compute(self, day: date) -> str:
        """Writes the session's row (once) and returns a one-line outcome."""
        readings = self._readings(day, marks(day))
        previous_day = previous_recorded_session(self.calendar, day)
        closing = self._readings(previous_day, marks(previous_day)[-1:])
        result = self.strategy.compute([level for level, _, _ in readings], closing[0][0])
        row = self._row(day, result, readings + closing)
        outcome = self.table.write_once(row)
        figure = f"RV {row['rv_session']} (vol {row['vol_pct']}%)" if row["status"] == OK else row["void_reason"]
        return f"{day} realised variance {outcome}: {row['status']}, {figure}"

    def has_row(self, day: date) -> bool:
        return any(row["session"] == day.isoformat() for row in self.table.rows())

    def void_share_line(self) -> str:
        rows = self.table.rows()
        void = sum(1 for r in rows if r["status"] == VOID)
        share = void / len(rows) if rows else 0.0
        flag = VOID_SHARE_FLAG if share > VOID_SHARE_LIMIT else ""
        return VOID_SHARE_LINE.format(void=void, total=len(rows), share=share, flag=flag)

    def _readings(self, day: date, wanted: list[datetime]) -> list[tuple[float | None, str, str]]:
        """Per wanted mark: its usable level (None where missing or unusable), the basis of that level, and the stored
        file's SHA-256 ("" when there is none)."""
        found = []
        for mark in wanted:
            data = self.store.get(snapshot_path(self.source, day, mark))
            doc = SnapshotDocument.from_bytes(data) if data else None
            level = index_check(doc).level if doc else None
            found.append((level, doc.index_basis if level is not None else "", _sha256(data)))
        return found

    def _row(self, day: date, result: RvResult, readings: list[tuple[float | None, str, str]]) -> dict:
        session_marks = marks(day)
        unusable = [label(session_marks[i]) for i in result.unusable_marks]
        reasons = ([f"no usable index level at {', '.join(unusable)}"] if unusable else []) + (
            ["no usable 15:30 level for the previous session"] if result.previous_close_missing else []
        )
        return {
            "session": day.isoformat(), "status": OK if result.session is not None else VOID,
            "rv_session": _figure(result.session), "rv_intraday": _figure(result.intraday),
            "rv_overnight": _figure(result.overnight),
            "vol_pct": "" if result.vol_pct is None else f"{result.vol_pct:.4f}", "void_reason": "; ".join(reasons),
            "good_slots": len(session_marks) - len(unusable), "due_slots": len(session_marks),
            "basis_counts": _basis_counts(readings[: len(session_marks)]),
            "measure": self.strategy.measure, "method": self.strategy.method, "source": self.source,
            "as_of": utc_text(session_marks[-1]), "first_seen_at": utc_text(self.now()),
            "inputs_sha256": hashlib.sha256("\n".join(sha for _, _, sha in readings).encode()).hexdigest(),
        }  # fmt: skip


def previous_recorded_session(calendar: SessionCalendar, day: date) -> date:
    """The session before `day` whose 15:30 level the overnight return starts from: the previous regular or special
    session (a muhurat evening hour has no 15:30 mark; its move falls inside the next overnight return)."""
    previous = calendar.previous_session(day)
    while calendar.session_kind(previous) not in RECORDED_SESSION_KINDS:
        previous = calendar.previous_session(previous)
    return previous


def _basis_counts(readings: list[tuple[float | None, str, str]]) -> str:
    """How many usable levels each rule gave, e.g. `candle_1m_close:26` (a session mixing rules is visible)."""
    counts = Counter(basis for level, basis, _ in readings if level is not None)
    return ";".join(f"{basis}:{count}" for basis, count in sorted(counts.items()))


def _sha256(data: bytes | None) -> str:
    return hashlib.sha256(data).hexdigest() if data else ""


def _figure(value: float | None) -> str:
    return "" if value is None else f"{value:.10f}"
