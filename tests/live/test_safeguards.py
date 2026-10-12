from dataclasses import replace
from datetime import date, timedelta

from fno import journal
from fno.config import load_config
from fno.constants import Direction, SessionPhase
from fno.live.contract_picker import ContractPicker, ExitLevels, PickerRules, max_planned_loss
from fno.live.kill_switch import KillSwitch
from fno.live.learning.performance import max_drawdown, performance_stop_reason, readiness_checks
from fno.live.models import MarketView
from fno.live.risk_gate import PortfolioGate
from fno.providers.sample import SampleProvider

from .fakes import SESSION_DAY, at

CFG = load_config(overrides={"profile": "live"})  # the conservative real-money limits


def idea(symbol="NIFTY"):
    chain = SampleProvider(CFG).chain(symbol, date(2026, 10, 27))
    picker = ContractPicker(
        PickerRules(min_open_interest=0), ExitLevels(), CFG["position_rules"], max_planned_loss(CFG)
    )
    found, reason = picker.pick(
        MarketView(symbol, Direction.BULLISH, 0.6, 0.8, strong_evidence=True), chain, SESSION_DAY
    )
    assert found, reason
    return found


def closed(pnl, closed_at, opened_at=None, underlying="TCS"):
    return {
        "status": "closed",
        "pnl_net": pnl,
        "closed_at": closed_at,
        "opened_at": opened_at or closed_at,
        "underlying": underlying,
        "entry_value": 100,
        "lot_size": 1,
        "lots": 1,
    }


def test_every_pick_fits_the_two_percent_risk_limit():
    for symbol in ("NIFTY", "BANKNIFTY"):
        found = idea(symbol)
        loss_at_stop = (found.entry_price - found.stop_price) * found.lot_size * found.lots
        assert loss_at_stop <= max_planned_loss(CFG) == 4000


def test_fast_decay_and_lottery_strikes_are_refused():
    expiry_morning = at(10, 0, date(2026, 10, 13))
    chain = SampleProvider(CFG, as_of=expiry_morning).chain("NIFTY", date(2026, 10, 13))  # hours left
    picker = ContractPicker(PickerRules(min_open_interest=0), ExitLevels(), CFG["position_rules"], 4000)
    years = chain.years_to_expiry()

    def problem(strike):
        quote = chain.get(strike, "CE")
        return picker._contract_problem(chain, quote, picker._greeks(chain, quote, years))

    assert problem(22500) == "time decay too fast"  # at the money on expiry morning
    assert problem(22550) in ("premium under Rs 20", "too far out of the money")  # a lottery ticket


def test_trade_frequency_and_loss_cooldown():
    gate = PortfolioGate(CFG, KillSwitch(__import__("pathlib").Path("/nonexistent/KILL")))
    new_idea = idea()
    two_today = [closed(100, f"2026-10-12T10:0{i}+05:30", underlying=f"S{i}") for i in range(2)]
    assert "2 new trades today" in gate.refusal(new_idea, two_today, SessionPhase.TRADING, at(11, 0))
    friday = date(2026, 10, 16)
    week = [
        closed(100, f"2026-10-{d:02d}T1{i}:00+05:30", underlying=f"S{d}{i}") for d in (12, 13, 14, 15) for i in (0, 1)
    ]
    assert "8 new trades this week" in gate.refusal(new_idea, week, SessionPhase.TRADING, at(11, 0, friday))
    last_week = [dict(t, opened_at=t["opened_at"].replace("2026-10-1", "2026-10-0")) for t in week]
    assert gate.refusal(new_idea, last_week, SessionPhase.TRADING, at(11, 0, friday)) is None  # a new week
    loser = [closed(-500, "2026-10-12T10:40+05:30", opened_at="2026-10-09T10:00+05:30")]
    assert "cooling off" in gate.refusal(new_idea, loser, SessionPhase.TRADING, at(11, 0))
    assert "cooling off" not in (gate.refusal(new_idea, loser, SessionPhase.TRADING, at(11, 30)) or "")


def test_weekly_loss_limit():
    monday = [closed(-7000, "2026-10-12T11:00+05:30"), closed(-5500, "2026-10-13T11:00+05:30")]
    assert "weekly loss limit" in journal.day_check(monday, CFG, date(2026, 10, 14))
    assert journal.day_check(monday, CFG, date(2026, 10, 19)) is None  # next week


def test_performance_stop():
    pnls = [500] * 5 + [-300] * 20
    trades = [closed(p, (at(10, 0) + timedelta(minutes=i)).isoformat()) for i, p in enumerate(pnls)]
    assert "last 20 trades" in performance_stop_reason(trades, CFG)
    assert max_drawdown([1000, -3000, 500, -1000]) == 3500
    assert performance_stop_reason(trades[:5], CFG) is None


def test_readiness_needs_a_long_profitable_record():
    trades = [closed(300 if i % 3 else -200, (at(10, 0) + timedelta(days=i)).isoformat()) for i in range(30)]
    checks = {c.name: c for c in readiness_checks(trades, CFG, SESSION_DAY + timedelta(days=40))}
    assert not checks["closed trades"].passed and checks["net profit after all charges"].passed


def test_correlated_trades_count_as_one_bet():
    gate = PortfolioGate(CFG, KillSwitch(__import__("pathlib").Path("/nonexistent/KILL")))
    gate.industries = {
        "HDFCBANK": "Financial Services",
        "ICICIBANK": "Financial Services",
        "TCS": "Information Technology",
    }
    holding = [
        dict(closed(0, "2026-10-09T10:00+05:30", underlying=u), status="open", closed_at=None, direction="bearish")
        for u in ("HDFCBANK", "ICICIBANK")
    ]
    bank_index = replace(idea(), underlying="BANKNIFTY")
    reason = gate.refusal(bank_index, holding, SessionPhase.TRADING, at(11, 0))
    assert reason and "Financial Services" in reason and "max 2" in reason
    it_stock = replace(idea(), underlying="TCS")
    assert gate.refusal(it_stock, holding, SessionPhase.TRADING, at(11, 0)) is None
    assert gate.family("UNKNOWNCO") == "UNKNOWNCO" and gate.family("NIFTY") == "broad market"
