import math
from datetime import date

from fno.config import load_config
from fno.providers.sample import SampleProvider
from fno.signals import compute_signals
from fno.strategies import build_candidates, select


def _setup():
    cfg = load_config(overrides={"strategies": {"iron_condor": True}})
    p = SampleProvider(cfg)
    chain = p.chain("NIFTY", date(2026, 10, 20))
    sig = compute_signals(p.context("NIFTY"), chain, cfg)
    return cfg, chain, sig, build_candidates(chain, sig, cfg)


def test_debit_spread_payoff_bounds():
    _, _, _, cands = _setup()
    bcs = next(c for c in cands if c.strategy == "bull_call_spread")
    width = bcs.legs[1].strike - bcs.legs[0].strike
    assert math.isclose(bcs.max_loss, bcs.entry_value, abs_tol=1e-6)
    assert math.isclose(bcs.max_profit, width - bcs.entry_value, abs_tol=1e-6)
    assert len(bcs.breakevens) == 1
    assert math.isclose(bcs.breakevens[0], bcs.legs[0].strike + bcs.entry_value, abs_tol=1.0)


def test_long_call_is_unbounded_and_condor_is_credit():
    _, _, _, cands = _setup()
    lc = next(c for c in cands if c.strategy == "long_call")
    assert math.isinf(lc.max_profit)
    ic = next(c for c in cands if c.strategy == "iron_condor")
    assert ic.entry_value < 0 and len(ic.breakevens) == 2


def test_market_ev_is_roughly_zero_minus_spread():
    # Under the market's own distribution there should be no free lunch.
    _, _, _, cands = _setup()
    for c in cands:
        assert c.ev_market < c.max_loss * 0.05


def test_select_respects_bias_direction():
    _, _, sig, cands = _setup()
    for c in select(cands, sig):
        assert c.direction == sig.label


def test_sizing_respects_budget():
    cfg, _, _, cands = _setup()
    budget = cfg["account"]["capital"] * cfg["account"]["risk_per_trade_pct"] / 100
    for c in cands:
        assert c.lots * c.risk_per_lot <= budget
