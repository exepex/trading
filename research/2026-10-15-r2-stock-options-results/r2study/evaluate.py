"""One structure on one event: fit, liquidity and expected net (PROTOCOL.md sections 5-6)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .bhav import Chain
from .rules import (
    ASSUMED_HURDLE,
    MAX_LOSS_CAP_RS,
    MIN_CONTRACTS_TRADED,
    MIN_OPEN_INTEREST_CONTRACTS,
    S7_TAIL_SHARE,
)
from .spreads import SpreadModel
from .structures import Strikes, Structure, maximum_loss, pads, price_structure, round_trip_charges


@dataclass(frozen=True)
class EventMarket:
    """What one event's analysis reads: the chosen expiry's chains on the entry session, on R (contracts traded and
    listed strikes only) and on the session before entry (the leg's liquidity tercile)."""

    symbol: str
    reaction: date
    sector: str | None
    lot: int
    strikes: Strikes
    entry: Chain
    exit: Chain
    previous: Chain


@dataclass(frozen=True)
class Outcome:
    structure: str
    untradable: str = ""
    price: float = 0.0
    charges: float = 0.0
    fits_without_pads: bool = False
    liquid: bool = False  # every leg: contracts on entry and exit, open interest on entry
    pads: float | None = None
    fits_with_pads: bool = False
    bucket_untradable: bool = False
    expected_net: float | None = None
    break_even_edge: float | None = None
    gross_to_cost: float | None = None

    @property
    def stage2(self) -> bool:
        return self.fits_without_pads and self.liquid

    @property
    def stage3(self) -> bool:
        """Fits the cap with pads, all legs liquid, no leg in an untradable bucket."""
        return self.fits_with_pads and self.liquid and not self.bucket_untradable

    @property
    def counts_for_clusters(self) -> bool:
        """Criteria 1 and 2 read per event (amendment 1 section A)."""
        return self.stage3 and (self.expected_net or 0.0) > 0


def leg_is_liquid(key: tuple[float, str], market: EventMarket) -> bool:
    entry, exit_leg = market.entry.get(key), market.exit.get(key)
    if entry is None or exit_leg is None:
        return False
    return (
        entry.contracts >= MIN_CONTRACTS_TRADED
        and exit_leg.contracts >= MIN_CONTRACTS_TRADED
        and entry.open_interest / market.lot >= MIN_OPEN_INTEREST_CONTRACTS
    )


def evaluate(structure: Structure, market: EventMarket, charges_table: dict, spreads: SpreadModel | None) -> Outcome:
    priced = price_structure(structure, market.entry, market.strikes)
    if priced.untradable:
        return Outcome(structure.name, untradable=priced.untradable, price=priced.price)
    lot = market.lot
    charges = round_trip_charges(priced, lot, charges_table)
    liquid = all(leg_is_liquid((strike, kind), market) for strike, kind, _, _ in priced.legs)
    base = dict(
        structure=structure.name,
        price=priced.price,
        charges=charges,
        fits_without_pads=maximum_loss(priced, lot, charges) <= MAX_LOSS_CAP_RS,
        liquid=liquid,
    )
    if spreads is None:
        return Outcome(**base)
    buckets = [
        spreads.bucket(steps, _previous_contracts(market, strike, kind))
        for steps, (strike, kind, _, _) in zip((spec.steps for spec in structure.legs), priced.legs, strict=True)
    ]
    bucket_untradable = any(b.untradable for b in buckets)
    if bucket_untradable:
        return Outcome(**base, bucket_untradable=True)
    padding = pads(priced, lot, [b.half_spread_p75 for b in buckets])
    cost = charges + padding
    loss = maximum_loss(priced, lot, cost)
    tail = S7_TAIL_SHARE * loss if structure.credit else 0.0
    notional = priced.price * lot
    gross = ASSUMED_HURDLE * notional
    return Outcome(
        **base,
        pads=padding,
        fits_with_pads=loss <= MAX_LOSS_CAP_RS,
        expected_net=gross - cost - tail,
        break_even_edge=(cost + tail) / notional,
        gross_to_cost=gross / (cost + tail) if cost + tail > 0 else None,
    )


def _previous_contracts(market: EventMarket, strike: float, kind: str) -> float:
    leg = market.previous.get((strike, kind))
    return leg.contracts if leg is not None else 0.0
