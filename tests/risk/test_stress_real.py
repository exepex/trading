"""Judge 43: on real quotes, a zero-move, zero-day scenario values every leg at its mark when the stress engine prices
with the same model the implied volatilities come from (B1's Black-76 on the same-expiry future).

12 Oct 2026, NIFTY October expiry (27 Oct), every strike within 300 points of the ATM strike 22,350 whose call and put
both traded: implied volatility from the traded close by Black-76, then repriced by the engine with no move.
"""

from datetime import date

import pytest

from fno.research_data.panel_reader import read_nifty_panel
from fno.research_engine.implied_vol import Black76, OptionPricing, SpotBlackScholes
from fno.risk.inputs import ContractQuote, Market
from fno.risk.stress import Shock, StressEngine
from fno.storage.wiring import PANEL_FOLDER

from .builders import LOT, contract

DAY, EXPIRY, ATM, RATE = date(2026, 10, 12), date(2026, 10, 27), 22350.0, 0.065
NO_MOVE = Shock("no_move", 0.0)


@pytest.fixture(scope="module")
def real_market() -> Market:
    panel = read_nifty_panel(PANEL_FOLDER, [2026], keep=lambda day, expiry: day == DAY and expiry == EXPIRY)
    spot, future = panel.session_on(DAY).underlying, panel.future_on(DAY, EXPIRY)
    forward, years = Black76().underlying(spot, future), (EXPIRY - DAY).days / 365
    quotes = {}
    for q in panel.options_on(DAY, EXPIRY):
        if abs(q.strike - ATM) > 300 or q.volume <= 0:
            continue
        iv = Black76().implied_vol(OptionPricing(q.close, forward, q.strike, q.kind, years, RATE))
        if iv is not None:
            quotes[contract(q.strike, q.kind, EXPIRY)] = ContractQuote(q.strike, q.kind, EXPIRY, q.close, iv)
    return Market(DAY, spot, RATE, quotes, {EXPIRY: future})


def test_a_zero_move_zero_day_scenario_values_every_real_leg_at_its_mark(real_market):
    engine = StressEngine(Black76())
    assert len(real_market.quotes) >= 20  # 11+ strikes, calls and puts
    for name, quote in real_market.quotes.items():
        error_per_lot = engine.leg_value(name, LOT, real_market, NO_MOVE) - LOT * quote.mid
        assert abs(error_per_lot) < 0.01, name  # under one paisa a lot


def test_spot_black_scholes_with_these_volatilities_would_be_off_by_about_rs_1000_a_lot(real_market):
    """The error judge 43 measured, kept as a guard: pricing on spot with Black-76 volatilities is not neutral."""
    spot_engine = StressEngine(SpotBlackScholes())
    errors = {
        quote.kind: spot_engine.leg_value(name, LOT, real_market, NO_MOVE) - LOT * quote.mid
        for name, quote in real_market.quotes.items()
        if quote.strike == ATM
    }
    assert errors["CE"] > 1000 and errors["PE"] < -1000
