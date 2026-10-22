"""`HistoricalChain` over the archived NSE F&O files (story MS-SIM-a): the first file that covers the day, current
format first, as the NIFTY panel and EDGE1 read them. Nothing is guessed: a lot is NSE's `NewBrdLotQty` where the file
states it, never derived from turnover; a day with no readable file, or none for the underlying, is None."""

from collections.abc import Callable, Sequence
from datetime import date

from ....constants import INDEX_FUTURE, INDEX_OPTION
from ....fo_bhavcopy import BadFile, read_fo_file
from ....research_data.nifty_panel import DailyFiles
from ...constants import OptionKind
from .ports import ChainRow, DayChain

IndexCloses = Callable[[date], float | None]


def _number(text: str) -> float:
    try:
        return float(text) if text not in ("", "-") else 0.0
    except ValueError:
        return 0.0


class BhavcopyChain:
    def __init__(self, fo_files: Sequence[DailyFiles], index_close: IndexCloses | None = None):
        self.fo_files, self.index_close = fo_files, index_close

    def day(self, underlying: str, session: date) -> DayChain | None:
        for files in self.fo_files:
            if not files.covers(session):
                continue
            name, data = files.get(session)
            if data is None:
                continue
            try:
                records = read_fo_file(name, data)
            except BadFile:
                continue
            chain = self._chain(session, underlying, records, files.label)
            if chain.rows:
                return chain
        return None

    def _chain(self, session: date, underlying: str, records: Sequence[dict], source: str) -> DayChain:
        mine = [r for r in records if r["TckrSymb"] == underlying and r["FinInstrmTp"] in (INDEX_OPTION, INDEX_FUTURE)]
        monthly = {_expiry(r) for r in mine if r["FinInstrmTp"] == INDEX_FUTURE}
        rows, lots, underlying_prices = [], {}, []
        for r in mine:
            expiry = _expiry(r)
            board = int(_number(r.get("NewBrdLotQty") or ""))
            if board > 0:
                lots.setdefault(expiry, board)
            if r["FinInstrmTp"] == INDEX_OPTION:
                rows.append(_row(r, expiry in monthly))
                underlying_prices.append(_number(r.get("UndrlygPric") or ""))
        return DayChain(session, underlying, self._close(session, underlying_prices), tuple(rows), lots, source)

    def _close(self, session: date, prices: list[float]) -> float | None:
        stated = next((p for p in prices if p > 0), None)
        return stated if stated is not None else (self.index_close(session) if self.index_close else None)


def _expiry(record: dict) -> date:
    return date.fromisoformat(record["XpryDt"][:10])


def _row(record: dict, monthly: bool) -> ChainRow:
    return ChainRow(
        _expiry(record), float(record["StrkPric"]), OptionKind(record["OptnTp"]), _number(record["ClsPric"]),
        int(_number(record["TtlTradgVol"])), int(_number(record["OpnIntrst"])), monthly,
    )  # fmt: skip
