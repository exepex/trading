"""A book's open positions as the desk sees them (story E4), derived from the two append-only records and never kept
as separate state: E1's cash ledger says which trades are still open and what they hold; the desk events say which of
them must be exited and which have unverified protection. A trade stops blocking the book once its last leg is closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..books.equity import TradePosition, trade_positions
from ..constants import (
    OUTCOME_EXIT_ORDERED,
    OUTCOME_NOT_OPENED,
    OUTCOME_OPENED,
    OUTCOME_PARTIAL_FILL,
    OUTCOME_PROTECTION_UNVERIFIED,
)
from .execution import Holding
from .records import DeskRecords

ENTRY_OUTCOMES = (OUTCOME_OPENED, OUTCOME_NOT_OPENED, OUTCOME_PARTIAL_FILL)


@dataclass(frozen=True)
class OpenPosition:
    trade_id: str
    decision_id: str
    holdings: tuple[Holding, ...]  # legs still held, with their units
    cash_flow: float  # E1: premium received minus paid, minus charges, so far
    last_fill_at: datetime
    opened_by: str  # snapshot ID of the trade's opening fills
    exit_reason: str  # why it must be exited (empty when no exit is ordered)
    protection_unverified: bool


def _holdings(trade: TradePosition, records: DeskRecords) -> tuple[Holding, ...]:
    legs = records.legs(trade.trade_id)
    missing = [c for c, units in trade.units.items() if units and c not in legs]
    if missing:
        raise ValueError(f"trade {trade.trade_id}: no desk fill record for {', '.join(missing)}")
    return tuple((legs[c], abs(units)) for c, units in sorted(trade.units.items()) if units)


def open_positions(records: DeskRecords) -> list[OpenPosition]:
    positions = []
    for trade in (t for t in trade_positions(records.account.fills()).values() if t.is_open):
        events, fills = records.event_rows(trade.trade_id), records.fill_rows(trade.trade_id)
        ordered = [e["reason"] for e in events if e["outcome"] == OUTCOME_EXIT_ORDERED]
        unverified = any(e["outcome"] == OUTCOME_PROTECTION_UNVERIFIED for e in events)
        positions.append(
            OpenPosition(
                trade.trade_id,
                fills[0]["decision_id"],
                _holdings(trade, records),
                trade.cash_flow,
                max(f.filled_at for f in trade.fills),
                fills[0]["snapshot_id"],
                ordered[0] if ordered else "",
                unverified,
            )  # fmt: skip
        )
    return positions


def unverified_trades(records: DeskRecords) -> list[str]:
    """Open trades of the book whose protection is unverified: while any is open, the book opens no new risk."""
    return [p.trade_id for p in open_positions(records) if p.protection_unverified]
