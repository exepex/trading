"""What the owner-timing clock and pricing give back (story E8): a due mark to fill at, or the reason an order missed.

The reasons are the fixed public wording of E8's rules; a reason never carries a price or a contract's quote."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

ENTRY, EXIT = "entry", "exit"

MISSED_NO_CARD = "missed, card not delivered"
MISSED_OWNER_AWAY = "missed, owner away"
MISSED_NO_QUOTE = "missed, no quote"
MISSED_PRICE_MOVED = "missed, price moved"
MISSED_EXPIRED = "missed, contract expired"
MISSED_FUNDS = "missed, insufficient funds"
MISSED_RISK_CAP = "missed, over risk cap"


@dataclass(frozen=True)
class DueMark:
    """Where an order fills: the session, the 15-minute mark (IST, time zone aware) and how many sessions it moved
    because the owner was away (rule 8)."""

    session: date
    mark: datetime
    away_moves: int = 0


@dataclass(frozen=True)
class Missed:
    reason: str
