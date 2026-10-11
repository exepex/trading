from datetime import date

from fno import journal
from fno.config import load_config
from fno.costs import order_charges
from fno.providers.sample import SampleProvider
from fno.signals import compute_signals
from fno.strategies import build_candidates


ALL = {k: True for k in ("bull_call_spread", "bear_put_spread", "long_call", "long_put")}


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
    cfg = load_config(overrides={"strategies": ALL})
    trades = []
    t = journal.open_trade(trades, _cand(cfg), cfg, lots=1)
    assert t["status"] == "open"
    log = journal.mark(trades, SampleProvider(cfg, spot_shift_pct=3.0), cfg, today=date(2026, 10, 12))
    assert trades[0]["status"] == "closed" and trades[0]["exit_reason"] == "target", log
    assert trades[0]["pnl_net"] > 0
    assert "win rate 100%" in journal.report(trades, cfg["account"]["capital"])


def test_paper_trade_stops_out_on_selloff():
    cfg = load_config(overrides={"strategies": ALL})
    trades = []
    journal.open_trade(trades, _cand(cfg), cfg, lots=1)
    journal.mark(trades, SampleProvider(cfg, spot_shift_pct=-3.0), cfg, today=date(2026, 10, 12))
    assert trades[0]["exit_reason"] == "stop loss" and trades[0]["pnl_net"] < 0


def test_unchanged_market_stays_open():
    cfg = load_config(overrides={"strategies": ALL})
    trades = []
    journal.open_trade(trades, _cand(cfg), cfg, lots=1)
    journal.mark(trades, SampleProvider(cfg), cfg, today=date(2026, 10, 12))
    assert trades[0]["status"] == "open" and trades[0]["last_mark"]["pnl"] < 0  # paid the spread


def test_max_open_trades_enforced():
    cfg = load_config(overrides={"account": {"max_open_trades": 1}, "strategies": ALL})
    trades = []
    journal.open_trade(trades, _cand(cfg), cfg)
    try:
        journal.open_trade(trades, _cand(cfg), cfg)
    except RuntimeError:
        return
    raise AssertionError("expected max_open_trades to block")


def test_html_report_renders_with_sample_data(tmp_path):
    from fno.brief import run_brief

    cfg = load_config(overrides={"provider": "sample"})
    md, _, _ = run_brief(SampleProvider(cfg), cfg, tmp_path, journal_stats=journal.stats([]), journal_log=[])
    html = (tmp_path / md.name.replace("-brief.md", "-brief.html")).read_text()
    page = (tmp_path / md.name.replace("-brief.md", "-page.html")).read_text()
    assert html.startswith("<!doctype html>") and "Jargon buster" in html and "<svg" in html
    assert not page.lstrip().startswith("<!doctype") and "<title>" in page[:8192]


def test_indian_rupee_grouping():
    from fno.html_report import inr

    assert inr(200000) == "₹2,00,000"
    assert inr(-6168) == "−₹6,168"
    assert inr(19832, sign=True) == "+₹19,832"


def _closed(pnl, at):
    return {"status": "closed", "pnl_net": pnl, "closed_at": at, "entry_value": 100, "lot_size": 65, "lots": 1}


def test_daily_brakes():
    cfg = load_config()
    day = date(2026, 10, 12)
    assert journal.day_check([], cfg, day) is None
    assert "loss limit" in journal.day_check([_closed(-5200, "2026-10-12T11:00")], cfg, day)
    assert "profit lock" in journal.day_check([_closed(6500, "2026-10-12T11:00")], cfg, day)
    losses = [_closed(-500, f"2026-10-12T1{i}:00") for i in range(3)]
    assert "in a row" in journal.day_check(losses, cfg, day)
    assert journal.day_check([_closed(-5200, "2026-10-09T11:00")], cfg, day) is None  # other day


def test_deployment_cap():
    cfg = load_config(overrides={"strategies": ALL})
    cand = _cand(cfg)
    trades = [dict(_closed(0, ""), status="open", entry_value=160, lot_size=65, lots=5)]  # Rs 52,000 deployed
    try:
        journal.open_trade(trades, cand, cfg, lots=1)
    except RuntimeError as e:
        assert "limit" in str(e)
        return
    raise AssertionError("expected the deployment cap to block")
