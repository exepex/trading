"""F1's gate inputs, point in time (protocol section 5): the parity forward and the ATM straddle's implied volatility
from the entry day's closes, and the EWMA forecast of realised volatility from index closes up to the session before
the entry session."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from fno.research_data.panel_reader import OptionQuote
from fno.research_engine.structures import atm_strike

LAMBDA, SEED_RETURNS, YEAR = 0.94, 20, 252
STRADDLE_FACTOR = math.sqrt(2 / math.pi)  # 0.7979: an ATM straddle is about this x F x sigma x sqrt(T)
GATES = {"G0": None, "G12": 1.2, "G15": 1.5}  # fixed before any ratio was seen
NO_FORWARD, NO_STRADDLE, NO_FORECAST = "no_forward", "no_straddle", "no_rv_forecast"


@dataclass(frozen=True)
class GateInputs:
    status: str  # "ok" or why the gate cannot be computed
    forward: float | None = None
    atm: float | None = None
    sigma_iv: float | None = None
    sigma_rv: float | None = None

    @property
    def ratio(self) -> float | None:
        return None if self.sigma_iv is None or not self.sigma_rv else self.sigma_iv / self.sigma_rv


def traded_pairs(quotes: Sequence[OptionQuote], expiry: date) -> dict[float, tuple[float, float]]:
    """strike -> (call close, put close) where both traded on the day."""
    calls = {q.strike: q.close for q in quotes if q.expiry == expiry and q.kind == "CE" and q.volume > 0}
    puts = {q.strike: q.close for q in quotes if q.expiry == expiry and q.kind == "PE" and q.volume > 0}
    return {k: (calls[k], puts[k]) for k in calls.keys() & puts.keys() if calls[k] > 0 and puts[k] > 0}


def forward_from(pairs: Mapping[float, tuple[float, float]], spot: float) -> float | None:
    if not pairs:
        return None
    k0 = atm_strike(pairs, spot)
    call, put = pairs[k0]
    return k0 + call - put


def implied(quotes: Sequence[OptionQuote], expiry: date, spot: float, n: int) -> GateInputs:
    pairs = traded_pairs(quotes, expiry)
    forward = forward_from(pairs, spot)
    if forward is None or forward <= 0:
        return GateInputs(NO_FORWARD)
    strikes = {q.strike for q in quotes if q.expiry == expiry}
    atm = atm_strike(strikes, forward)
    if atm not in pairs:
        return GateInputs(NO_STRADDLE, forward, atm)
    call, put = pairs[atm]
    return GateInputs("ok", forward, atm, (call + put) / (STRADDLE_FACTOR * forward * math.sqrt(n / YEAR)))


def ewma_sigma(closes: Sequence[float]) -> float | None:
    """Annualised EWMA volatility of the log returns of `closes` (oldest first), seeded with the variance of the first
    SEED_RETURNS returns; None with too few closes."""
    returns = [math.log(b / a) for a, b in zip(closes, closes[1:]) if a > 0 and b > 0]
    if len(returns) <= SEED_RETURNS:
        return None
    variance = sum(r * r for r in returns[:SEED_RETURNS]) / SEED_RETURNS
    for r in returns[SEED_RETURNS:]:
        variance = LAMBDA * variance + (1 - LAMBDA) * r * r
    return math.sqrt(YEAR * variance)


def gate_inputs(quotes, expiry: date, spot: float, n: int, closes_before: Sequence[float]) -> GateInputs:
    """`closes_before`: the index's closes from 1 Jan 2018 up to the session before the entry session."""
    found = implied(quotes, expiry, spot, n)
    if found.status != "ok":
        return found
    sigma_rv = ewma_sigma(closes_before)
    if sigma_rv is None:
        return GateInputs(NO_FORECAST, found.forward, found.atm, found.sigma_iv)
    return GateInputs("ok", found.forward, found.atm, found.sigma_iv, sigma_rv)


def passes(gate: str, inputs: GateInputs) -> bool:
    level = GATES[gate]
    return level is None or (inputs.ratio is not None and inputs.ratio >= level)
