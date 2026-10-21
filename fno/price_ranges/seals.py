"""Seals recorded once (part A5; review finding 1): GitHub's activity log only reaches back a week, so a seal is read
while it exists and kept as a write-once seal file in Drive, with its own receipt. A known push time (on time or
late) is final; unknown evidence is retried until the record is older than the log's reach, then recorded late.
Readers use the stored seal, and only compute one for a record not yet sealed."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date, datetime, timedelta

from ..price_distribution.store import DistributionStore
from .folders import live_path, seal_path
from .sealing import Seal, SealCheck

LOG_REACH = timedelta(days=7)  # GitHub's activity log: `time_period=week` (fno/ai/receipts.py)
EXPIRED = "late: no push evidence while GitHub's 7-day activity log still covered it ({why})"
STORED = "{underlying} {day} {issue}: seal stored ({state})"
PENDING = "{underlying} {day} {issue}: seal pending ({why})"


def _encode(seal: Seal) -> bytes:
    fields = {"sealed_at": seal.sealed_at.isoformat() if seal.sealed_at else None,
              "deadline": seal.deadline.isoformat() if seal.deadline else None, "late": seal.late,
              "reason": seal.reason}  # fmt: skip
    return (json.dumps(fields, sort_keys=True, indent=1) + "\n").encode()


def _decode(data: bytes) -> Seal:
    fields = json.loads(data)

    def moment(text):
        return datetime.fromisoformat(text) if text else None

    return Seal(moment(fields["sealed_at"]), moment(fields["deadline"]), fields["late"], fields["reason"])


class Seals:
    def __init__(self, check: SealCheck, store: DistributionStore, receipt_of: Callable[[str], str],
                 now: Callable[[], datetime]):  # fmt: skip
        """`receipt_of(drive path)`: the repository path of that file's receipt."""
        self.check, self.store, self.receipt_of, self.now = check, store, receipt_of, now

    def seal(self, underlying: str, day: date, issue: str) -> Seal:
        stored = self.store.get(seal_path(underlying, day, issue))
        if stored is not None:
            return _decode(stored)
        return self.check.seal(self.receipt_of(live_path(underlying, day, issue)), day)

    def record(self, underlying: str, day: date, issue: str) -> str | None:
        """Stores the seal when it is final; returns a line, or None when it was already stored."""
        path = seal_path(underlying, day, issue)
        if self.store.get(path) is not None:
            return None
        seal = self.check.seal(self.receipt_of(live_path(underlying, day, issue)), day)
        if seal.sealed_at is None:
            if self.now().date() - day <= LOG_REACH:
                return PENDING.format(underlying=underlying, day=day, issue=issue, why=seal.reason)
            seal = Seal(None, seal.deadline, True, EXPIRED.format(why=seal.reason))
        self.store.put(path, _encode(seal))
        state = "late" if seal.late else f"sealed at {seal.sealed_at.isoformat()}"
        return STORED.format(underlying=underlying, day=day, issue=issue, state=state)


def seal_recent(seals: Seals, has_record: Callable[[str, date, str], bool], underlyings, issue: str,
                day: date) -> list[str]:  # fmt: skip
    """Records every final seal of the live issues of the last 8 calendar days before `day` (inside GitHub's log)."""
    lines = []
    for offset in range(1, LOG_REACH.days + 2):
        past = day - timedelta(days=offset)
        for underlying in underlyings:
            if has_record(underlying, past, issue):
                line = seals.record(underlying, past, issue)
                lines += [line] if line else []
    return lines
