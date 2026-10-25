"""F8's two-leg credit spreads (protocol section 5) and their trades through EDGE1's frozen EXP path (held to
settlement, C1's charges, the entry pad, the cap, the impossible-price rule). The entry prices are the legs' opening
trades: each quote's `close` field carries the open, so EDGE1's code prices the entry at the open unchanged."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from edge1study.trade import EXP, Trade, run_trade

from fno.constants import OPTION_CALL, OPTION_PUT
from fno.research_data.panel_reader import NiftyPanel, OptionQuote, SessionClose
from fno.research_engine.cycle_costs import LOSS_CAP, CycleTerms
from fno.research_engine.cycles import Cycle
from fno.research_engine.structures import BOUGHT, SOLD, Leg, Structure, atm_strike, nearest_strike

VARIANTS = {"P0W5": (0.0, 0.005), "P5W5": (0.005, 0.005), "P0W10": (0.0, 0.01)}  # (distance, width) of F
PUT, CALL = "put", "call"


class CreditSpread(Structure):
    """Sell the short leg `distance` out of the money from the forward, buy the long leg `width` beyond it (both as
    fractions of the forward, snapped to listed strikes). The `width` argument of `legs` is ignored: it is fixed."""

    def __init__(self, side: str, distance: float, width: float):
        self.side, self.distance, self.width, self.code = side, distance, width, f"{side}_credit"

    def build(self, strikes: set[float], spot: float, _width: float) -> list[Leg]:
        sign = -1 if self.side == PUT else 1
        target = spot * (1 + sign * self.distance)
        short = atm_strike(strikes, spot) if self.distance == 0 else nearest_strike(strikes, target, self.side == CALL)
        far = [k for k in strikes if (k - short) * sign > 0]
        if not far:
            return [Leg(short, self._kind(), SOLD), Leg(short, self._kind(), BOUGHT)]  # refused by the cap check
        long_ = nearest_strike(far, short + sign * self.width * spot, self.side == CALL)
        return [Leg(short, self._kind(), SOLD), Leg(long_, self._kind(), BOUGHT)]

    def _kind(self) -> str:
        return OPTION_PUT if self.side == PUT else OPTION_CALL


@dataclass(frozen=True)
class EntryQuote:
    strike: float
    kind: str
    open: float
    close: float
    volume: int


def as_quotes(entries: Sequence[EntryQuote], expiry: date, at_open: bool) -> tuple[OptionQuote, ...]:
    """Engine quotes priced at the open (or the close, the sensitivity run); an untraded leg has volume 0."""
    return tuple(OptionQuote(expiry, e.strike, e.kind, e.open if at_open else e.close, 0.0, e.volume, 0)
                 for e in entries)  # fmt: skip


def spread_trade(variant: str, side: str, entry_day: date, expiry: date, quotes: Sequence[OptionQuote], forward: float,
                 lot: int, settlement: float, charges: Mapping[str, float], pad: float) -> Trade:  # fmt: skip
    distance, width = VARIANTS[variant]
    panel = NiftyPanel((SessionClose(entry_day, "regular", forward, None),), {entry_day: tuple(quotes)}, {})
    terms = CycleTerms(lot, dict(charges), pad, LOSS_CAP, (width * forward,))
    return run_trade(CreditSpread(side, distance, width), panel, Cycle(expiry, entry_day, entry_day, expiry), terms,
                     EXP, [entry_day, expiry], lambda _e: settlement, capped=True)  # fmt: skip
