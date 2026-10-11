from datetime import date
from pathlib import Path

from fno.config import load_config
from fno.constants import Direction, ExitReason, SessionPhase
from fno.live.contract_picker import ContractPicker, ExitLevels, PickerRules
from fno.live.exit_policy import ExitPolicy
from fno.live.kill_switch import KillSwitch
from fno.live.market_clock import MarketClock, SessionTimes
from fno.live.models import MarketView
from fno.live.risk_gate import PortfolioGate
from fno.live.universe import choose_expiry
from fno.providers.sample import SampleProvider

from .fakes import SESSION_DAY, at

CLOCK = MarketClock(SessionTimes(), holidays={date(2026, 10, 20)})


def view(direction=Direction.BULLISH, strong=False):
    return MarketView("NIFTY", direction, 0.6 if direction is Direction.BULLISH else -0.6, 0.8, strong_evidence=strong)


def test_session_phases():
    assert CLOCK.phase(at(8, 50)) is SessionPhase.CLOSED
    assert CLOCK.phase(at(9, 5)) is SessionPhase.PRE_OPEN
    assert CLOCK.phase(at(9, 20)) is SessionPhase.OPENING_RANGE
    assert CLOCK.phase(at(11, 0)) is SessionPhase.TRADING
    assert CLOCK.phase(at(14, 50)) is SessionPhase.NO_NEW_ENTRIES
    assert CLOCK.phase(at(15, 20)) is SessionPhase.SQUARE_OFF
    assert CLOCK.phase(at(11, 0, date(2026, 10, 20))) is SessionPhase.CLOSED  # holiday
    assert CLOCK.phase(at(11, 0, date(2026, 10, 17))) is SessionPhase.CLOSED  # Saturday


def test_holding_days_and_previous_close():
    assert CLOCK.trading_days_held(date(2026, 10, 16), date(2026, 10, 19)) == 2  # Fri -> Mon
    assert CLOCK.previous_session_close(at(10, 0)).date() == date(2026, 10, 9)


def trade(expiry="2026-10-27", opened="2026-10-12T10:00+05:30"):
    return {"entry_value": 100.0, "stop_amount": 30.0, "target_amount": 60.0, "expiry": expiry, "opened_at": opened}


def test_exit_policy():
    policy = ExitPolicy(CLOCK, max_holding_days=2, exit_days_before_expiry=1)
    assert policy.exit_reason(trade(), 69.0, at(11, 0), SessionPhase.TRADING) is ExitReason.STOP_LOSS
    assert policy.exit_reason(trade(), 161.0, at(11, 0), SessionPhase.TRADING) is ExitReason.TARGET
    assert policy.exit_reason(trade(), 110.0, at(15, 16), SessionPhase.SQUARE_OFF) is None  # day 1 of 2
    day2 = at(15, 16, date(2026, 10, 13))
    assert policy.exit_reason(trade(), 110.0, day2, SessionPhase.SQUARE_OFF) is ExitReason.MAX_HOLDING_DAYS
    near_expiry = trade(expiry="2026-10-13")
    assert policy.exit_reason(near_expiry, 110.0, at(15, 16), SessionPhase.SQUARE_OFF) is ExitReason.BEFORE_EXPIRY


def test_choose_expiry_keeps_away_from_expiry_day():
    expiries = [date(2026, 10, 13), date(2026, 10, 20), date(2026, 10, 27)]
    assert choose_expiry(expiries, SESSION_DAY, 4) == date(2026, 10, 20)
    assert choose_expiry(expiries, date(2026, 10, 26), 4) is None


def picker(cfg):
    return ContractPicker(PickerRules(min_open_interest=0), ExitLevels(), cfg["position_rules"])


def test_picker_buys_calls_for_bullish_and_puts_for_bearish():
    cfg = load_config()
    chain = SampleProvider(cfg).chain("NIFTY", date(2026, 10, 27))
    call, _ = picker(cfg).pick(view(Direction.BULLISH, strong=True), chain, SESSION_DAY)
    put, _ = picker(cfg).pick(view(Direction.BEARISH, strong=True), chain, SESSION_DAY)
    assert call.option_kind == "CE" and put.option_kind == "PE"
    assert call.contract_name.startswith("NIFTY 27 Oct ") and call.contract_name.endswith(" Call")
    assert call.stop_price == round(call.entry_price * 0.7, 2) and call.target_price == round(call.entry_price * 1.6, 2)
    assert call.capital_used <= cfg["position_rules"]["exception_max_per_trade"]


def test_picker_refuses_pricey_lot_without_strong_evidence():
    cfg = load_config()
    chain = SampleProvider(cfg).chain("BANKNIFTY", date(2026, 10, 27))  # one lot well above Rs 11,000
    idea, reason = picker(cfg).pick(view(strong=False), chain, SESSION_DAY)
    assert idea is None and "evidence" in reason


def test_picker_skips_neutral():
    cfg = load_config()
    chain = SampleProvider(cfg).chain("NIFTY", date(2026, 10, 27))
    assert picker(cfg).pick(view(Direction.NEUTRAL), chain, SESSION_DAY)[0] is None


def test_portfolio_gate(tmp_path: Path):
    cfg = load_config()
    chain = SampleProvider(cfg).chain("NIFTY", date(2026, 10, 27))
    idea, _ = picker(cfg).pick(view(strong=True), chain, SESSION_DAY)
    switch = KillSwitch(tmp_path / "KILL")
    gate = PortfolioGate(cfg, switch)
    assert gate.refusal(idea, [], SessionPhase.TRADING, at(11, 0)) is None
    assert "no new entries" in gate.refusal(idea, [], SessionPhase.NO_NEW_ENTRIES, at(14, 50))
    holding = [{"status": "open", "underlying": "NIFTY", "entry_value": 50, "lot_size": 65, "lots": 1}]
    assert "already holding" in gate.refusal(idea, holding, SessionPhase.TRADING, at(11, 0))
    recent = [{"status": "closed", "underlying": "NIFTY", "closed_at": "2026-10-12T10:50+05:30", "pnl_net": 10}]
    assert "less than" in gate.refusal(idea, recent, SessionPhase.TRADING, at(11, 0))
    full = [{"status": "open", "underlying": f"S{i}", "entry_value": 10, "lot_size": 1, "lots": 1} for i in range(5)]
    assert "already open" in gate.refusal(idea, full, SessionPhase.TRADING, at(11, 0))
    bullish = [
        {"status": "open", "underlying": f"S{i}", "direction": "bullish", "entry_value": 10, "lot_size": 1, "lots": 1}
        for i in range(3)
    ]
    assert "bullish trades open" in gate.refusal(idea, bullish, SessionPhase.TRADING, at(11, 0))
    indices = [
        {"status": "open", "underlying": u, "direction": "bearish", "entry_value": 10, "lot_size": 1, "lots": 1}
        for u in ("BANKNIFTY", "FINNIFTY")
    ]
    assert "index trades" in gate.refusal(idea, indices, SessionPhase.TRADING, at(11, 0))
    switch.engage("test", at(11, 0))
    assert "kill switch" in gate.refusal(idea, [], SessionPhase.TRADING, at(11, 0))
