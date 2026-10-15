"""The time part of `C` (PROTOCOL.md section 9): the Black-76 value change from the decision time to the fill time with
only time moving. Forward and each leg's IV are held at the decision; time is calendar minutes to 15:30 IST on the
expiry day over 365 x 1440. A leg with no IV makes the whole time part None ("not computed"), never filled in."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import date, datetime, time

from fno.research_engine.implied_vol import Black76, ImpliedVolModel, OptionPricing
from fno.research_engine.structures import Leg

EXPIRY_CLOSE = time(15, 30)
MINUTES_A_YEAR = 365 * 1440


def years_to_expiry(at: datetime, expiry: date) -> float:
    return (datetime.combine(expiry, EXPIRY_CLOSE) - at).total_seconds() / 60 / MINUTES_A_YEAR


def time_part(legs: Sequence[Leg], prices: Sequence[float], forward: float, decided: datetime, filled: datetime,
              expiry: date, rate: float, model: ImpliedVolModel | None = None) -> float | None:  # fmt: skip
    model = model or Black76()
    start, end = years_to_expiry(decided, expiry), years_to_expiry(filled, expiry)
    total = 0.0
    for leg, price in zip(legs, prices, strict=True):
        option = OptionPricing(price, forward, leg.strike, leg.kind, start, rate)
        sigma = model.implied_vol(option)
        if sigma is None:
            return None
        total += leg.side * (model.price(replace(option, years=end), sigma) - model.price(option, sigma))
    return total
