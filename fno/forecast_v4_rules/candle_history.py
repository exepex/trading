"""W8's one reader of A16b's candle-close history (owner, 24 Oct 2026: "W8 - yes"; story G7b completion): each
session's row of A16b's `rv-candle/` table, of A16b's pinned method and `backfilled` provenance only (any other row is
not read), void kept void. Yardstick A's ratio window (`pack_wiring.intraday_rv`), G8's W8 drift line and story G14
read it here and nowhere else; never a forecast input, outcome or base rate (decision 56 as the owner read it)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from ..global_cues.table import BACKFILLED
from ..intraday.realised_vol import CandleCloseRv15m
from .series import A16_OK

W8_CANDLE_METHOD = CandleCloseRv15m.method  # "rv-candle-15m-v1"


@dataclass(frozen=True)
class CandleSession:
    day: date
    status: str  # A16's "ok" or "void"
    rv_session: float | None  # None when void (never a value)
    method: str
    provenance: str
    first_seen_at: datetime


def candle_sessions(rows: list[dict]) -> list[CandleSession]:
    """A16b's rows (`CandleRvTable.rows()`) of the pinned method and provenance, in session order."""
    return sorted(
        (
            CandleSession(
                date.fromisoformat(r["session"]),
                r["status"],
                float(r["rv_session"]) if r["status"] == A16_OK else None,
                r["method"],
                r["provenance"],
                datetime.fromisoformat(r["first_seen_at"]),
            )  # fmt: skip
            for r in rows
            if r.get("method") == W8_CANDLE_METHOD and r.get("provenance") == BACKFILLED
        ),
        key=lambda s: s.day,
    )
