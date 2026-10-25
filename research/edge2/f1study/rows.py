"""One index's rows of a day's archived NSE F&O file for F1 (protocol section 3): its options of the nearest two
expiries on or after the day (enough for a weekly cycle's entry and for seeing an expiry trade on its own day), its
futures, and each expiry's market lot. EDGE1's `day_files.rows_of` keeps monthly options only; this keeps weeklies.
The lot rule is EDGE1's (UDiFF `NewBrdLotQty`, else derived, which `lots.py` only checks)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from edge1study.day_files import DayRows, _number, _whole, derived_lot

from fno.constants import INDEX_FUTURE, INDEX_OPTION
from fno.research_data.panel_reader import FutureQuote, OptionQuote

KEPT_EXPIRIES = 2


def _option(r: dict, expiry: date) -> OptionQuote:
    return OptionQuote(expiry, float(r["StrkPric"]), r["OptnTp"], _number(r["ClsPric"]), _number(r["SttlmPric"]),
                       _whole(r["TtlTradgVol"]), _whole(r["OpnIntrst"]))  # fmt: skip


def symbol_rows(day: date, records: Sequence[dict], symbol: str, source: str) -> DayRows:
    """The symbol's futures, lots and the options of its nearest KEPT_EXPIRIES expiries on or after `day`."""
    options, futures, lots = [], [], {}
    for r in records:
        if r["TckrSymb"] != symbol or r["FinInstrmTp"] not in (INDEX_OPTION, INDEX_FUTURE):
            continue
        expiry = date.fromisoformat(r["XpryDt"][:10])
        board = _whole(r.get("NewBrdLotQty") or "")
        if board > 0:
            lots.setdefault(expiry, board)
        if r["FinInstrmTp"] == INDEX_OPTION:
            if expiry >= day:
                options.append(_option(r, expiry))
            continue
        futures.append(FutureQuote(expiry, _number(r["ClsPric"]), _number(r["SttlmPric"]), _whole(r["TtlTradgVol"]),
                                   _whole(r["OpnIntrst"])))  # fmt: skip
        if expiry not in lots:
            found = derived_lot(_number(r["TtlTrfVal"]), _whole(r["TtlTradgVol"]), _number(r["SttlmPric"]))
            if found:
                lots[expiry] = found
    nearest = set(sorted({q.expiry for q in options})[:KEPT_EXPIRIES])
    kept = tuple(q for q in options if q.expiry in nearest)
    return DayRows(day, kept, tuple(futures), lots, source)
