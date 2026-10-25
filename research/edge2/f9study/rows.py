"""F9's day rows (protocol section 4): an index's options of its nearest two monthly expiries (an expiry with a
future listed that day) on or after the day, its futures with their open and close (the open gives the overnight
gap), and each expiry's lot, from a day's archived F&O file. The lot rule is EDGE1's (UDiFF `NewBrdLotQty`, else
EDGE1's circular schedule, applied by the caller)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from edge1study.day_files import _number, _whole

from fno.constants import INDEX_FUTURE, INDEX_OPTION
from fno.research_data.panel_reader import OptionQuote

KEPT_MONTHLIES = 2


@dataclass(frozen=True)
class FutureBar:
    expiry: date
    open: float
    close: float


@dataclass(frozen=True)
class MonthlyDay:
    day: date
    options: tuple[OptionQuote, ...]
    futures: tuple[FutureBar, ...]
    lots: dict[date, int]  # UDiFF board lots only; empty in legacy files
    source: str


def monthly_rows(day: date, records: Sequence[dict], symbol: str, source: str) -> MonthlyDay:
    options, futures, lots = [], [], {}
    for r in records:
        if r["TckrSymb"] != symbol or r["FinInstrmTp"] not in (INDEX_OPTION, INDEX_FUTURE):
            continue
        expiry = date.fromisoformat(r["XpryDt"][:10])
        board = _whole(r.get("NewBrdLotQty") or "")
        if board > 0:
            lots.setdefault(expiry, board)
        if r["FinInstrmTp"] == INDEX_FUTURE:
            futures.append(FutureBar(expiry, _number(r["OpnPric"]), _number(r["ClsPric"])))
        elif expiry >= day:
            close, settle = _number(r["ClsPric"]), _number(r["SttlmPric"])
            volume, oi = _whole(r["TtlTradgVol"]), _whole(r["OpnIntrst"])
            options.append(OptionQuote(expiry, float(r["StrkPric"]), r["OptnTp"], close, settle, volume, oi))
    monthly = sorted({f.expiry for f in futures if f.expiry >= day})[:KEPT_MONTHLIES]
    kept = tuple(q for q in options if q.expiry in monthly)
    return MonthlyDay(day, kept, tuple(sorted(futures, key=lambda f: f.expiry)), lots, source)
