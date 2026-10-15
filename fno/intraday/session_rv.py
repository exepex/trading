"""Computes a finished session's realised variance from the snapshots stored in Drive (story A16): each mark's index
level is judged by the same rule as when it was taken (`status.index_check`), the strategy computes the figure, and the
row is written once. Also reports the share of void sessions (design 5.2: above 5%, a new version is proposed)."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import date, datetime

from ..models import IST, now_ist
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
        levels, hashes = self._levels(day, marks(day))
        previous, previous_hashes = self._levels(*_closing_marks(self.calendar, day))
        result = self.strategy.compute(levels, previous[-1])
        row = self._row(day, result, hashes + previous_hashes)
        outcome = self.table.write_once(row)
        figure = f"RV {row['rv_session']} (vol {row['vol_pct']}%)" if row["status"] == OK else row["void_reason"]
        return f"{day} realised variance {outcome}: {row['status']}, {figure}"

    def void_share_line(self) -> str:
        rows = self.table.rows()
        void = sum(1 for r in rows if r["status"] == VOID)
        share = void / len(rows) if rows else 0.0
        flag = VOID_SHARE_FLAG if share > VOID_SHARE_LIMIT else ""
        return VOID_SHARE_LINE.format(void=void, total=len(rows), share=share, flag=flag)

    def _levels(self, day: date, wanted: list[datetime]) -> tuple[list[float | None], list[str]]:
        """Each wanted mark's usable level (None where missing or unusable) and its stored file's SHA-256 ("" if
        none). The repeat check compares each mark with the one before it in `wanted`."""
        levels: list[float | None] = []
        hashes: list[str] = []
        previous_level = None
        for mark in wanted:
            data = self.store.get(snapshot_path(self.source, day, mark))
            hashes.append(hashlib.sha256(data).hexdigest() if data else "")
            doc = SnapshotDocument.from_bytes(data) if data else None
            levels.append(index_check(doc, previous_level).level if doc else None)
            previous_level = doc.index_level if doc else None
        return levels, hashes

    def _row(self, day: date, result: RvResult, hashes: list[str]) -> dict:
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
            "good_marks": len(session_marks) - len(unusable), "due_marks": len(session_marks),
            "measure": self.strategy.measure, "method": self.strategy.method, "source": self.source,
            "as_of": session_marks[-1].astimezone(IST).isoformat(), "first_seen_at": utc_text(self.now()),
            "inputs_sha256": hashlib.sha256("\n".join(hashes).encode()).hexdigest(),
        }  # fmt: skip


def previous_recorded_session(calendar: SessionCalendar, day: date) -> date:
    """The session before `day` whose 15:30 level the overnight return starts from: the previous regular or special
    session (a muhurat evening hour has no 15:30 mark; its move falls inside the next overnight return)."""
    previous = calendar.previous_session(day)
    while calendar.session_kind(previous) not in RECORDED_SESSION_KINDS:
        previous = calendar.previous_session(previous)
    return previous


def _closing_marks(calendar: SessionCalendar, day: date) -> tuple[date, list[datetime]]:
    """The previous recorded session and its 15:15 and 15:30 marks (15:15 only for the repeat check of 15:30)."""
    previous = previous_recorded_session(calendar, day)
    return previous, marks(previous)[-2:]


def _figure(value: float | None) -> str:
    return "" if value is None else f"{value:.10f}"
