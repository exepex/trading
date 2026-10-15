"""Stock futures and stock options of one session, from NSE's daily F&O file (either format, via fno.fo_bhavcopy).

Two reads: `summarise` keeps every stock future and the set of stocks with options (small, for every session);
`option_legs` keeps the option legs of chosen stocks (only on the sessions an event needs).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from fno.fo_bhavcopy import read_fo_file

STOCK_FUTURE, STOCK_OPTION = "STF", "STO"


@dataclass(frozen=True)
class Future:
    expiry: date
    close: float
    settle: float
    contracts: float
    turnover: float  # rupees
    open_interest: float  # shares
    lot: int | None  # the current format's lot column; None in the legacy format


@dataclass(frozen=True)
class Leg:
    close: float
    contracts: float
    open_interest: float  # shares
    lot: int | None = None  # the current format's lot column of this contract; None in the legacy format


@dataclass
class DaySummary:
    day: date
    futures: dict[str, list[Future]] = field(default_factory=dict)  # symbol -> its futures, nearest expiry first
    option_symbols: frozenset[str] = frozenset()

    def near_future(self, symbol: str, on_or_after: date | None = None) -> Future | None:
        """The future with the nearest expiry on or after a day (the session itself by default)."""
        floor = on_or_after or self.day
        return next((f for f in self.futures.get(symbol, []) if f.expiry >= floor), None)

    def future(self, symbol: str, expiry: date) -> Future | None:
        """The stock future of one expiry."""
        return next((f for f in self.futures.get(symbol, []) if f.expiry == expiry), None)

    def is_fo_stock(self, symbol: str) -> bool:
        """Point-in-time F&O eligibility: both stock futures and stock options listed on the session."""
        return symbol in self.futures and symbol in self.option_symbols


Chain = dict[tuple[float, str], Leg]  # (strike, "CE" or "PE") -> leg


def number(text: str) -> float:
    return float(text) if text not in ("", "-") else 0.0


def lot_column(text: str) -> int | None:
    """A lot of 0 or an empty column is unknown, never a lot."""
    value = int(float(text)) if text not in ("", "-") else 0
    return value if value > 0 else None


def summarise(day: date, filename: str, data: bytes, symbol_of=lambda s, d: s) -> DaySummary:
    """Every stock future and the stocks with options; `symbol_of(symbol, day)` maps a session's symbol to the
    study's one name for the company (symbol changes)."""
    futures: dict[str, list[Future]] = defaultdict(list)
    with_options = set()
    for r in read_fo_file(filename, data):
        kind = r["FinInstrmTp"]
        if kind == STOCK_OPTION:
            with_options.add(symbol_of(r["TckrSymb"], day))
        elif kind == STOCK_FUTURE:
            futures[symbol_of(r["TckrSymb"], day)].append(
                Future(
                    expiry=date.fromisoformat(r["XpryDt"]),
                    close=number(r["ClsPric"]),
                    settle=number(r["SttlmPric"]),
                    contracts=number(r["TtlTradgVol"]),
                    turnover=number(r["TtlTrfVal"]),
                    open_interest=number(r["OpnIntrst"]),
                    lot=lot_column(r["NewBrdLotQty"]),
                )
            )
    ordered = {s: sorted(fs, key=lambda f: f.expiry) for s, fs in futures.items()}
    return DaySummary(day, ordered, frozenset(with_options))


def option_legs(
    day: date, filename: str, data: bytes, symbols: set[str], symbol_of=lambda s, d: s
) -> dict[str, dict[date, Chain]]:
    """symbol -> expiry -> chain, for the chosen stocks only."""
    out: dict[str, dict[date, Chain]] = defaultdict(lambda: defaultdict(dict))
    for r in read_fo_file(filename, data):
        if r["FinInstrmTp"] != STOCK_OPTION:
            continue
        symbol = symbol_of(r["TckrSymb"], day)
        if symbol not in symbols:
            continue
        leg = Leg(number(r["ClsPric"]), number(r["TtlTradgVol"]), number(r["OpnIntrst"]), lot_column(r["NewBrdLotQty"]))
        out[symbol][date.fromisoformat(r["XpryDt"])][(float(r["StrkPric"]), r["OptnTp"])] = leg
    return {s: dict(chains) for s, chains in out.items()}
