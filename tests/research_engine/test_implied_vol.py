"""Implied-volatility models (story B1 note of 13 Oct 2026): Black-76 on the same-expiry future."""

from datetime import date

import pytest
from feature_fixtures import black76

from fno.research_data.panel_reader import FutureQuote, read_nifty_panel
from fno.research_engine.implied_vol import Black76, OptionPricing, SpotBlackScholes
from fno.research_engine.volatility_features import atm_strike, traded_close
from fno.storage.wiring import PANEL_FOLDER

RATE = 0.065


@pytest.mark.parametrize("kind", ["CE", "PE"])
@pytest.mark.parametrize("sigma", [0.05, 0.15, 0.6, 1.5])
def test_black76_recovers_the_volatility_of_a_textbook_price(kind, sigma):
    price = black76(22400.0, 22300.0, 30 / 365, sigma, kind)
    vol = Black76().implied_vol(OptionPricing(price, 22400.0, 22300.0, kind, 30 / 365, RATE))
    assert vol == pytest.approx(sigma, abs=1e-6)


@pytest.mark.parametrize("price", [0.0, -1.0, 1e-6, 30000.0])
def test_no_volatility_outside_the_bounds(price):
    assert Black76().implied_vol(OptionPricing(price, 22400.0, 22300.0, "CE", 30 / 365, RATE)) is None


def test_no_volatility_at_or_after_expiry():
    assert Black76().implied_vol(OptionPricing(100.0, 22400.0, 22300.0, "CE", 0.0, RATE)) is None


def test_each_model_names_the_price_it_is_written_on():
    traded, untraded = FutureQuote(date(2026, 10, 27), 22386.5, 22386.5, 10, 1), None
    assert Black76().underlying(22363.35, traded) == 22386.5
    assert Black76().underlying(22363.35, traded._replace(volume=0)) is None  # never the settlement of no trade
    assert Black76().underlying(22363.35, untraded) is None
    assert SpotBlackScholes().underlying(22363.35, traded) == 22363.35


DAY = date(2026, 10, 12)
EXPIRIES = (date(2026, 10, 27), date(2026, 11, 23))


@pytest.fixture(scope="module")
def chain_12_oct_2026():
    return read_nifty_panel(PANEL_FOLDER, [2026], keep=lambda day, expiry: day == DAY and expiry in EXPIRIES)


def call_put_gap(panel, model, expiry, strike):
    """Call IV minus put IV at one strike, in volatility points (both legs traded)."""
    spot = panel.session_on(DAY).underlying
    quotes, years = panel.options_on(DAY, expiry), (expiry - DAY).days / 365
    underlying = model.underlying(spot, panel.future_on(DAY, expiry))
    vols = [
        model.implied_vol(OptionPricing(traded_close(quotes, strike, kind), underlying, strike, kind, years, RATE))
        for kind in ("CE", "PE")
    ]
    return (vols[0] - vols[1]) * 100


@pytest.mark.parametrize("expiry", EXPIRIES)
def test_call_and_put_iv_agree_within_half_a_point_at_the_atm_strike_on_12_oct_2026(chain_12_oct_2026, expiry):
    """A real liquid day: Black-76 on the future gives 0.04 (Oct) and -0.11 (Nov) points; spot Black-Scholes with
    6.5% splits them by -2.00 and -1.39 points (the split the option-chain mockup found)."""
    panel = chain_12_oct_2026
    strike = atm_strike(panel.options_on(DAY, expiry), panel.session_on(DAY).underlying)
    assert strike == 22350.0
    assert abs(call_put_gap(panel, Black76(), expiry, strike)) < 0.5
    assert abs(call_put_gap(panel, SpotBlackScholes(), expiry, strike)) > 1.0


def test_black76_agrees_within_half_a_point_at_every_liquid_strike_near_the_money(chain_12_oct_2026):
    """Every strike within 300 points of ATM whose call and put both traded 1,000+ contracts (Oct: 11 strikes)."""
    panel, expiry = chain_12_oct_2026, EXPIRIES[0]
    quotes = panel.options_on(DAY, expiry)
    volume = {(q.strike, q.kind): q.volume for q in quotes}
    liquid = [
        k for k in {q.strike for q in quotes} if abs(k - 22350) <= 300 and min(volume[k, "CE"], volume[k, "PE"]) >= 1000
    ]
    assert len(liquid) == 11
    assert max(abs(call_put_gap(panel, Black76(), expiry, k)) for k in liquid) < 0.5
