"""One index's rows of a day's archived NSE F&O file (protocol sections 3 and 8), in the engine's own quote types: every
option and future of the index with close, settlement, volume and open interest, and each expiry's market lot.

The lot is UDiFF's `NewBrdLotQty` when the file carries it. Otherwise it is derived from the same-expiry future as
round(turnover / (contracts x settlement price)), R2's rule (`r2study/lots.py: derived_lot`), here in the F&O file's own
columns. The first archived file that has the day is used, current format first, as the NIFTY panel does."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from fno.constants import INDEX_FUTURE, INDEX_OPTION
from fno.fo_bhavcopy import BadFile, read_fo_file
from fno.research_data.nifty_panel import DailyFiles
from fno.research_data.panel_reader import FutureQuote, OptionQuote


@dataclass(frozen=True)
class DayRows:
    day: date
    options: tuple[OptionQuote, ...]
    futures: tuple[FutureQuote, ...]
    lots: dict[date, int]  # expiry -> units per lot
    source: str  # the file's dataset label (udiff or legacy)


def _number(text: str) -> float:
    try:
        return float(text) if text not in ("", "-") else 0.0
    except ValueError:
        return 0.0


def _whole(text: str) -> int:
    return int(_number(text))


def derived_lot(turnover: float, contracts: int, settle: float) -> int | None:
    """R2's rule: round(turnover / (contracts x settlement price)) of the same-expiry future; None without trades."""
    if contracts <= 0 or settle <= 0 or turnover <= 0:
        return None
    return round(turnover / (contracts * settle))


def rows_of(day: date, records: Sequence[dict], symbol: str, source: str) -> DayRows:
    options, futures, lots = [], [], {}
    for r in records:
        if r["TckrSymb"] != symbol or r["FinInstrmTp"] not in (INDEX_OPTION, INDEX_FUTURE):
            continue
        expiry = date.fromisoformat(r["XpryDt"][:10])
        close, settle = _number(r["ClsPric"]), _number(r["SttlmPric"])
        volume, oi = _whole(r["TtlTradgVol"]), _whole(r["OpnIntrst"])
        board = _whole(r.get("NewBrdLotQty") or "")
        if board > 0:
            lots.setdefault(expiry, board)
        if r["FinInstrmTp"] == INDEX_OPTION:
            options.append(OptionQuote(expiry, float(r["StrkPric"]), r["OptnTp"], close, settle, volume, oi))
        else:
            futures.append(FutureQuote(expiry, close, settle, volume, oi))
            if expiry not in lots:
                found = derived_lot(_number(r["TtlTrfVal"]), volume, settle)
                if found:
                    lots[expiry] = found
    return DayRows(day, tuple(options), tuple(futures), lots, source)


def day_rows(fo_files: Sequence[DailyFiles], day: date, symbols: Sequence[str]) -> dict[str, DayRows]:
    """Each symbol's rows from the first archived file that has the day; an empty dict when no file has it."""
    for files in fo_files:
        if not files.covers(day):
            continue
        name, data = files.get(day)
        if data is None:
            continue
        try:
            records = read_fo_file(name, data)
        except BadFile:
            continue
        found = {s: rows_of(day, records, s, files.label) for s in symbols}
        if any(r.options or r.futures for r in found.values()):
            return found
    return {}
