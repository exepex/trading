"""One entry at one reaction time (PROTOCOL.md sections 6, 7, 9, 10 and 14): the legs' prices at the decision and at
E8's fill, `C = V_fill - V_decision` (positive is worse for the trader), its risk scale, its time part, the split keys
and the two settled P&Ls for the flip share. A stale or missing leg leaves the structure out, with its reason; no other
price ever stands in."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import date, time

from fno.constants import STRUCTURES_BOUGHT_ONLY
from fno.research_engine.structures import position_value

from .bars import Bar
from .contracts import future_symbol, option_symbol
from .entries import Entry, IndexLevels
from .flips import settled_pnl
from .timepart import time_part
from .times import Moment, fill_moment, is_e4_snapshot, nights

WIDTH_UNAVAILABLE = "width unavailable (a leg not listed)"
MISSING = "leg candle missing"
STALE = "leg candle stale (zero volume)"
NO_DEBIT = "long option price not above zero"


@dataclass(frozen=True)
class Observation:
    family: str
    width: int
    decision: time
    reaction: int
    day: date
    expiry: date
    sessions_to_expiry: int
    nights: int
    e4_snapshot: bool
    excluded: str | None = None
    c: float | None = None
    risk: float | None = None
    time_part: float | None = None  # None: not computed
    gap: float | None = None  # |index at fill / index at decision - 1|; None: index missing at the fill
    vix: float | None = None  # India VIX open of the decision day
    pnl_decision: float | None = None  # None: expiry not settled
    pnl_fill: float | None = None


@dataclass(frozen=True)
class Market:
    bar: Callable[[str, Moment], Bar | None]  # a contract's candle ending at a moment
    index: IndexLevels
    vix_open: Mapping[date, float]
    settlement: Mapping[date, float]
    next_session: Callable[[date], date]


@dataclass(frozen=True)
class Terms:
    lot: int
    charges: dict
    rate: float


class Observer:
    def __init__(self, market: Market, terms: Terms):
        self.market, self.terms = market, terms

    def observe(self, entry: Entry, reaction: int) -> Observation:
        fill = fill_moment(entry.decision, reaction, self.market.next_session)
        base = Observation(entry.family, entry.width, entry.decision.at, reaction, entry.day.day, entry.day.expiry,
                           entry.day.sessions_to_expiry, nights(entry.decision, fill),
                           is_e4_snapshot(fill, entry.decision))  # fmt: skip
        decided, why = self.leg_prices(entry, entry.decision)
        filled, why = (None, why) if why else self.leg_prices(entry, fill)
        if why:
            return replace(base, excluded=why)
        risk = position_value(entry.legs, decided) if entry.family in STRUCTURES_BOUGHT_ONLY else float(entry.width)
        if risk <= 0:
            return replace(base, excluded=NO_DEBIT)
        return replace(base, c=position_value(entry.legs, filled) - position_value(entry.legs, decided), risk=risk,
                     time_part=self._time_part(entry, decided, fill), gap=self._gap(entry, fill),
                     vix=self.market.vix_open.get(entry.day.day), **self._pnls(entry, decided, filled))  # fmt: skip

    def leg_prices(self, entry: Entry, moment: Moment) -> tuple[list[float] | None, str | None]:
        if entry.legs is None:
            return None, WIDTH_UNAVAILABLE
        bars = [self.market.bar(option_symbol(entry.day.expiry, leg.strike, leg.kind), moment) for leg in entry.legs]
        if any(bar is None for bar in bars):
            return None, MISSING
        if any(bar.stale for bar in bars):
            return None, STALE
        return [bar.close for bar in bars], None

    def _time_part(self, entry: Entry, decided: list[float], fill: Moment) -> float | None:
        forward = self.market.bar(future_symbol(entry.day.expiry), entry.decision)
        if forward is None or forward.stale:
            return None
        return time_part(entry.legs, decided, forward.close, entry.decision.naive, fill.naive, entry.day.expiry,
                         self.terms.rate)  # fmt: skip

    def _gap(self, entry: Entry, fill: Moment) -> float | None:
        later = self.market.index.level(fill)
        return None if later is None else abs(later / entry.spot - 1)

    def _pnls(self, entry: Entry, decided: list[float], filled: list[float]) -> dict:
        settlement = self.market.settlement.get(entry.day.expiry)
        if settlement is None:
            return {}
        lot, charges = self.terms.lot, self.terms.charges
        return {"pnl_decision": settled_pnl(entry.legs, decided, settlement, lot, charges),
                "pnl_fill": settled_pnl(entry.legs, filled, settlement, lot, charges)}  # fmt: skip
