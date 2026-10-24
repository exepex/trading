"""EDGE1's structures (protocol section 5). The tradeable set is the engine's own: SC2 is `ShortCondor()`, SC3 is
`ShortCondor(0.03)` and SF is `ShortIronFly()`, unchanged.

The two naked measurements (the owner's Q1 answer: "also measure", never nominated) are built here, outside the engine
and its tradable list. They have the same strikes as SC2's shorts and SF's body, without wings. They are the only
structures anywhere that skip `require_covered`, and only this study's runner builds them."""

from __future__ import annotations

from fno.constants import OPTION_CALL, OPTION_PUT
from fno.research_engine.structures import SOLD, Chain, Leg, ShortCondor, ShortIronFly, Structure, atm_strike

SC2, SC3, SF, NS, NT = "SC2", "SC3", "SF", "NS", "NT"
TRADEABLE = (SC2, SC3, SF)
MEASURED = (NS, NT)  # "not tradeable under the house rules"
NOT_TRADEABLE = "not tradeable under the house rules"


class NakedBody(Structure):
    """A sold call and a sold put and nothing bought: `legs` skips the engine's covered check on purpose."""

    def legs(self, chain: Chain, spot: float, width: float) -> list[Leg] | None:
        strikes = {strike for strike, _ in chain}
        if not strikes:
            return None
        legs = self.build(strikes, spot, width)
        return legs if all(leg.contract in chain for leg in legs) else None

    def build(self, strikes: set[float], spot: float, width: float) -> list[Leg]:
        call, put = self.body_strikes(strikes, spot)
        return [Leg(call, OPTION_CALL, SOLD), Leg(put, OPTION_PUT, SOLD)]

    def body_strikes(self, strikes: set[float], spot: float) -> tuple[float, float]:
        raise NotImplementedError


class NakedStrangle(NakedBody):
    """NS: SC2's two shorts (the call nearest spot x 1.02, the put nearest spot x 0.98)."""

    code = NS

    def body_strikes(self, strikes: set[float], spot: float) -> tuple[float, float]:
        return ShortCondor().body_strikes(strikes, spot)


class NakedStraddle(NakedBody):
    """NT: SF's ATM call and put."""

    code = NT

    def body_strikes(self, strikes: set[float], spot: float) -> tuple[float, float]:
        atm = atm_strike(strikes, spot)
        return atm, atm


def structure(code: str) -> Structure:
    return {SC2: ShortCondor(), SC3: ShortCondor(0.03), SF: ShortIronFly(), NS: NakedStrangle(),
            NT: NakedStraddle()}[code]  # fmt: skip
