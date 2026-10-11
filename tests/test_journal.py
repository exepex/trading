from datetime import date

from fno import journal
from fno.config import load_config
from fno.costs import order_charges
from fno.providers.sample import SampleProvider
from fno.signals import compute_signals
from fno.strategies import build_candidates


def _cand(cfg):
    p = SampleProvider(cfg)
    chain = p.chain("NIFTY", date(2026, 10, 20))
    sig = compute_signals(p.context("NIFTY"), chain, cfg)
    c = next(c for c in build_candidates(chain, sig, cfg) if c.strategy == "bull_call_spread")
    return c.to_dict()


def test_charges_sell_side_includes_stt():
    ch = load_config()["charges"]
    assert order_charges(100, 65, "sell", ch) > order_charges(100, 65, "buy", ch)


def test_paper_trade_hits_target_on_rally():
    cfg = load_config()
    trades = []
    t = journal.open_trade(trades, _cand(cfg), cfg, lots=1)
    assert t["status"] == "open"
    log = journal.mark(trades, SampleProvider(cfg, spot_shift_pct=3.0), cfg, today=date(2026, 10, 12))
    assert trades[0]["status"] == "closed" and trades[0]["exit_reason"] == "target", log
    assert trades[0]["pnl_net"] > 0
    assert "win rate 100%" in journal.report(trades, cfg["account"]["capital"])


def test_paper_trade_stops_out_on_selloff():
    cfg = load_config()
    trades = []
    journal.open_trade(trades, _cand(cfg), cfg, lots=1)
    journal.mark(trades, SampleProvider(cfg, spot_shift_pct=-3.0), cfg, today=date(2026, 10, 12))
    assert trades[0]["exit_reason"] == "stop loss" and trades[0]["pnl_net"] < 0


def test_unchanged_market_stays_open():
    cfg = load_config()
    trades = []
    journal.open_trade(trades, _cand(cfg), cfg, lots=1)
    journal.mark(trades, SampleProvider(cfg), cfg, today=date(2026, 10, 12))
    assert trades[0]["status"] == "open" and trades[0]["last_mark"]["pnl"] < 0  # paid the spread


def test_max_open_trades_enforced():
    cfg = load_config(overrides={"account": {"max_open_trades": 1}})
    trades = []
    journal.open_trade(trades, _cand(cfg), cfg)
    try:
        journal.open_trade(trades, _cand(cfg), cfg)
    except RuntimeError:
        return
    raise AssertionError("expected max_open_trades to block")
