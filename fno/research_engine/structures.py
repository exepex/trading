"""Experiment 1's protected structures (story B2, protocol section 4): four legs, a body and two wings W points out.

Strikes: the nearest listed strike to the target; on an equal-distance tie the ATM strike is the lower one (as in F1)
and a short out-of-the-money leg takes the strike farther from spot (more conservative). A wing W points away must be
listed exactly, otherwise that width is unavailable. Every structure has one call and one put bought for each one sold,
so its terminal payoff is flat beyond the outer strikes and its extremes lie at strikes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass

from ..constants import (
    OPTION_CALL,
    OPTION_PUT,
    STRUCTURE_LONG_IRON_FLY,
    STRUCTURE_SHORT_CONDOR,
    STRUCTURE_SHORT_IRON_FLY,
)

BOUGHT, SOLD = 1, -1
CONDOR_OFFSET = 0.02  # SC sells the call nearest spot x 1.02 and the put nearest spot x 0.98

Contract = tuple[float, str]  # (strike, "CE" or "PE")
Chain = frozenset[Contract]  # the contracts of one expiry listed on one day


@dataclass(frozen=True)
class Leg:
    strike: float
    kind: str  # "CE" or "PE"
    side: int  # BOUGHT (+1) or SOLD (-1) when the position is opened

    @property
    def contract(self) -> Contract:
        return self.strike, self.kind

    @property
    def bought(self) -> bool:
        return self.side == BOUGHT

    def intrinsic(self, underlying: float) -> float:
        gap = underlying - self.strike if self.kind == OPTION_CALL else self.strike - underlying
        return max(gap, 0.0)


def terminal_value(legs: Iterable[Leg], underlying: float) -> float:
    """What the position is worth per unit at expiry with the index at `underlying` (bought legs count plus)."""
    return sum(leg.side * leg.intrinsic(underlying) for leg in legs)


def nearest_strike(strikes: Iterable[float], target: float, tie_higher: bool) -> float:
    """The listed strike nearest `target`; an equal-distance tie goes to the higher strike if `tie_higher`."""
    return min(strikes, key=lambda k: (abs(k - target), -k if tie_higher else k))


class Structure(ABC):
    """A body (a call and a put on `body_side`) with a wing `width` points further out on the other side."""

    code: str
    body_side: int

    def legs(self, chain: Chain, spot: float, width: float) -> list[Leg] | None:
        """The four legs for this width, or None when a needed contract is not listed (the width is unavailable)."""
        strikes = {strike for strike, _ in chain}
        if not strikes:
            return None
        call, put = self.body_strikes(strikes, spot)
        legs = [
            Leg(call, OPTION_CALL, self.body_side),
            Leg(put, OPTION_PUT, self.body_side),
            Leg(call + width, OPTION_CALL, -self.body_side),
            Leg(put - width, OPTION_PUT, -self.body_side),
        ]
        return legs if all(leg.contract in chain for leg in legs) else None

    @abstractmethod
    def body_strikes(self, strikes: set[float], spot: float) -> tuple[float, float]:
        """The body's (call strike, put strike)."""


class IronFly(Structure, ABC):
    """Body at the ATM strike: the listed strike nearest spot, the lower one on a tie."""

    def body_strikes(self, strikes: set[float], spot: float) -> tuple[float, float]:
        atm = nearest_strike(strikes, spot, tie_higher=False)
        return atm, atm


class ShortIronFly(IronFly):
    """SF: sell the ATM call and put, buy each W away."""

    code, body_side = STRUCTURE_SHORT_IRON_FLY, SOLD


class LongIronFly(IronFly):
    """BF: buy the ATM call and put, sell each W away."""

    code, body_side = STRUCTURE_LONG_IRON_FLY, BOUGHT


class ShortCondor(Structure):
    """SC: sell the call nearest spot x 1.02 and the put nearest spot x 0.98, buy each W further out."""

    code, body_side = STRUCTURE_SHORT_CONDOR, SOLD

    def body_strikes(self, strikes: set[float], spot: float) -> tuple[float, float]:
        call = nearest_strike(strikes, spot * (1 + CONDOR_OFFSET), tie_higher=True)
        put = nearest_strike(strikes, spot * (1 - CONDOR_OFFSET), tie_higher=False)
        return call, put
