"""What the fleet reads of a ledger (story MS-P1j): its recorded entries, read-only. Open positions and each
position's opening fill are derived from them, so settlement runs before the session's first `view` (judge 486's
note: a view writes the session's equity row) and an outcome names its own entry fill."""

from typing import Protocol

from ..contracts.accounts import LedgerEntry
from ..contracts.decisions import OpenPosition


class LedgerReader(Protocol):
    def entries(self, driver_id: str) -> tuple[LedgerEntry, ...]: ...


def open_positions(entries: tuple[LedgerEntry, ...]) -> tuple[OpenPosition, ...]:
    closed = {e.position.position_id for e in entries if e.closes}
    return tuple(e.position for e in entries if not e.closes and e.position.position_id not in closed)


def opening_of(entries: tuple[LedgerEntry, ...], position_id: str) -> LedgerEntry:
    found = [e for e in entries if not e.closes and e.position.position_id == position_id]
    if len(found) != 1:
        raise LookupError(f"{position_id}: {len(found)} opening entries in its ledger")
    return found[0]
