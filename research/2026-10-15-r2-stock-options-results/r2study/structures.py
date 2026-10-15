"""The seven structures of PROTOCOL.md section 5: strikes, prices, charges and maximum loss, 1 lot."""

from __future__ import annotations

from dataclasses import dataclass

from fno.constants import SIDE_BUY, SIDE_SELL
from fno.costs import order_charges

from .bhav import Chain, Leg

CALL, PUT = "CE", "PE"
NO_STRIKE, UNPRICED, DEBIT_AT_WIDTH, NOT_POSITIVE = (
    "no listed strike",
    "leg with close 0 or no contracts",
    "price at least the width (debit spread) or the wider wing (condor credit)",
    "price not positive",
)


@dataclass(frozen=True)
class LegSpec:
    steps: int  # strike = K0 + steps x the step in that direction (0 for K0)
    kind: str
    sign: int  # +1 bought, -1 sold


@dataclass(frozen=True)
class Structure:
    name: str
    legs: tuple[LegSpec, ...]
    credit: bool = False
    spread_width: int = 0  # S5/S6: the debit must stay below this many steps' width


STRUCTURES = (
    Structure("S1 bought call", (LegSpec(0, CALL, 1),)),
    Structure("S2 bought put", (LegSpec(0, PUT, 1),)),
    Structure("S3 long straddle", (LegSpec(0, CALL, 1), LegSpec(0, PUT, 1))),
    Structure("S4 long strangle", (LegSpec(1, CALL, 1), LegSpec(-1, PUT, 1))),
    Structure("S5 bull call spread", (LegSpec(0, CALL, 1), LegSpec(1, CALL, -1)), spread_width=1),
    Structure("S6 bear put spread", (LegSpec(0, PUT, 1), LegSpec(-1, PUT, -1)), spread_width=1),
    Structure(
        "S7 short iron condor",
        (LegSpec(1, CALL, -1), LegSpec(2, CALL, 1), LegSpec(-1, PUT, -1), LegSpec(-2, PUT, 1)),
        credit=True,
    ),
)


@dataclass(frozen=True)
class Strikes:
    k0: float
    up: float | None  # gap from K0 to the next listed strike above
    down: float | None  # and below

    def strike(self, steps: int) -> float | None:
        step = self.up if steps >= 0 else self.down
        if steps and step is None:
            return None
        return round(self.k0 + steps * (step or 0.0), 2)


def atm_strikes(chain: Chain, underlying: float) -> Strikes | None:
    """K0: the listed strike nearest the underlying (ties to the higher); the steps to its listed neighbours."""
    listed = sorted({strike for strike, _ in chain})
    if not listed:
        return None
    k0 = min(listed, key=lambda k: (abs(k - underlying), -k))
    above = [k for k in listed if k > k0]
    below = [k for k in listed if k < k0]
    return Strikes(k0, above[0] - k0 if above else None, k0 - below[-1] if below else None)


@dataclass(frozen=True)
class Priced:
    """A structure on one event: its legs (strike, kind, sign, entry leg) or the reason it cannot be traded."""

    structure: Structure
    legs: tuple[tuple[float, str, int, Leg], ...] = ()
    price: float = 0.0  # debit, or the credit for S7
    width: float = 0.0  # S5/S6: the spread's width; S7: the wider wing
    untradable: str = ""


def price_structure(structure: Structure, chain: Chain, strikes: Strikes) -> Priced:
    legs = []
    for spec in structure.legs:
        strike = strikes.strike(spec.steps)
        leg = chain.get((strike, spec.kind)) if strike is not None else None
        if leg is None:
            return Priced(structure, untradable=NO_STRIKE)
        if leg.close <= 0 or leg.contracts <= 0:
            return Priced(structure, untradable=UNPRICED)
        legs.append((strike, spec.kind, spec.sign, leg))
    net = sum(sign * leg.close for _, _, sign, leg in legs)
    price = -net if structure.credit else net
    width = _width(structure, legs)
    if price <= 0:
        return Priced(structure, tuple(legs), price, width, NOT_POSITIVE)
    if (structure.spread_width or structure.credit) and price >= width:
        return Priced(structure, tuple(legs), price, width, DEBIT_AT_WIDTH)
    return Priced(structure, tuple(legs), price, width)


def _width(structure: Structure, legs: list) -> float:
    if structure.credit:
        calls = sorted(k for k, kind, _, _ in legs if kind == CALL)
        puts = sorted(k for k, kind, _, _ in legs if kind == PUT)
        return max(calls[-1] - calls[0], puts[-1] - puts[0])
    if structure.spread_width:
        strikes = [k for k, _, _, _ in legs]
        return max(strikes) - min(strikes)
    return 0.0


def round_trip_charges(priced: Priced, lot: int, charges: dict) -> float:
    """C1 charges of every leg on entry and on exit, the exit charged on the entry price (exit prices are not read)."""
    total = 0.0
    for _, _, sign, leg in priced.legs:
        opening, closing = (SIDE_BUY, SIDE_SELL) if sign > 0 else (SIDE_SELL, SIDE_BUY)
        total += order_charges(leg.close, lot, opening, charges) + order_charges(leg.close, lot, closing, charges)
    return total


def pads(priced: Priced, lot: int, half_spreads: list[float]) -> float:
    """One pad per leg per side: the leg's bucket half-spread x its entry price x lot, twice (entry and exit)."""
    return sum(2 * h * leg.close * lot for (_, _, _, leg), h in zip(priced.legs, half_spreads, strict=True))


def maximum_loss(priced: Priced, lot: int, costs: float) -> float:
    """Debit structures: the debit; the iron condor: the wider wing less the credit. Costs added."""
    loss_per_unit = priced.width - priced.price if priced.structure.credit else priced.price
    return loss_per_unit * lot + costs
