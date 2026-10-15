"""The live "moved after cutoff" flag (story G10, protocol section 1.6): A16's index levels at its 14:30 and 15:15
marks, each read from the Drive copy its ledger row names, checked against the row's SHA-256 and judged by A16's own
level rule (`status.index_check`), the rule X was calibrated with. A missing row, copy or usable level, or a Drive read
that fails, leaves the flag not computable (None: flag, never block); a copy whose bytes differ from its row stops the
report."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import date, datetime, time

from ...forecast_v4.cutoff_move import cutoff_move, moved_after_cutoff
from ...forecast_v4.terms import V4_CAPTURE_START, V4_COMMON_SNAPSHOT
from ...intraday.document import SnapshotDocument, utc_text
from ...intraday.ledger import SlotLedger
from ...intraday.status import index_check
from ...models import IST
from ...storage.raw_store import RawFileStore


class SnapshotChanged(RuntimeError):
    """A Drive copy whose SHA-256 is not the one its ledger row recorded."""


class CutoffMoves(ABC):
    @abstractmethod
    def moved(self, day: date) -> bool | None:
        """Whether the day moved more than X from 14:30 to 15:15; None when it cannot be computed."""


class NoCutoffLevels(CutoffMoves):
    """Without the owner's Drive settings no level can be read: every flag is not computable."""

    def moved(self, day: date) -> bool | None:
        return None


class A16CutoffMoves(CutoffMoves):
    def __init__(self, ledger: SlotLedger, store: RawFileStore, x: float):
        self.ledger, self.store, self.x = ledger, store, x

    def moved(self, day: date) -> bool | None:
        start, end = self.level(day, V4_CAPTURE_START), self.level(day, V4_COMMON_SNAPSHOT)
        return None if start is None or end is None else moved_after_cutoff(cutoff_move(start, end), self.x)

    def level(self, day: date, at: time) -> float | None:
        key = utc_text(datetime.combine(day, at, IST))
        row = next((r for r in self.ledger.rows(day) if r["mark"] == key and r["raw_path"]), None)
        try:
            data = self.store.get(row["raw_path"]) if row else None
        except Exception:  # noqa: BLE001 - a Drive outage never blocks the report; the day counts as not computable
            return None
        if data is None:
            return None
        if hashlib.sha256(data).hexdigest() != row["raw_sha256"]:
            raise SnapshotChanged(f"{row['raw_path']}: its bytes are not the ones its ledger row recorded")
        return index_check(SnapshotDocument.from_bytes(data)).level
