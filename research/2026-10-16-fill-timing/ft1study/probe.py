"""The coverage probe (PROTOCOL.md section 3, run before the freeze): for each monthly expiry, does Groww answer
15-minute candles for that month's near-ATM call and its future? It records only the symbol and the candle count, never
a price, and archives nothing. A month that does not answer is tried again with the next strike."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from fno.research_engine.structures import atm_strike

from .candles import CandleCallFailed, ContractCandles
from .contracts import MonthlyContracts, future_symbol, option_symbol

PROBE_SESSIONS_BEFORE_EXPIRY = 10  # the probed day: about the middle of the window an expiry is used in
STRIKE_STEP_TRIES = (0, 50)  # points from ATM: the ATM call, then the next strike up
FIELDS = ("expiry", "kind", "symbol", "answered", "candles", "note")


@dataclass(frozen=True)
class ProbeRow:
    expiry: date
    kind: str  # "option" or "future"
    symbol: str
    candles: int
    note: str

    @property
    def answered(self) -> bool:
        return self.candles > 0

    def as_row(self) -> list[str]:
        return [self.expiry.isoformat(), self.kind, self.symbol, str(self.answered), str(self.candles), self.note]


def probe(contracts: MonthlyContracts, expiries: list[date], source: ContractCandles,
          sessions_before: Callable[[date, int], date]) -> list[ProbeRow]:  # fmt: skip
    """`sessions_before(expiry, n)`: the session n sessions before expiry."""
    found = []
    for expiry in expiries:
        day = sessions_before(expiry, PROBE_SESSIONS_BEFORE_EXPIRY)
        chain = contracts.listed[expiry].get(day, frozenset())
        atm = atm_strike({strike for strike, _ in chain}, contracts.closes[day]) if chain else None
        found.append(_first_answer(expiry, day, atm, source))
        found.append(_row(expiry, "future", future_symbol(expiry), day, source, ""))
    return found


def _first_answer(expiry: date, day: date, atm: float | None, source: ContractCandles) -> ProbeRow:
    if atm is None:
        return ProbeRow(expiry, "option", "", 0, f"no listed chain on {day}")
    tried = []
    for step in STRIKE_STEP_TRIES:
        row = _row(expiry, "option", option_symbol(expiry, atm + step, "CE"), day, source, "; ".join(tried))
        if row.answered:
            return row
        tried.append(f"{row.symbol}: {row.note or 'no candles'}")
    return ProbeRow(expiry, "option", row.symbol, 0, "; ".join(tried))


def _row(expiry: date, kind: str, symbol: str, day: date, source: ContractCandles, note: str) -> ProbeRow:
    try:
        answer = source.candles(symbol, day, day)
    except CandleCallFailed as failure:
        return ProbeRow(expiry, kind, symbol, 0, str(failure))
    return ProbeRow(expiry, kind, symbol, len(answer.rows), note)
