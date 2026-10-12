from datetime import date, datetime, timedelta

from fno.backtest.option_model import OptionModel
from fno.backtest.report import format_report
from fno.backtest.simulator import Backtester, sessions_of
from fno.config import load_config
from fno.live.exit_policy import ExitPolicy, TrailingStop
from fno.live.market_clock import MarketClock, SessionTimes
from fno.live.market_view import MarketViewBuilder, ViewThresholds
from fno.live.models import Candle
from fno.live.signals.base import SignalRule
from fno.models import IST

CFG = load_config()


class AlwaysBullish(SignalRule):
    name = "always_bullish"

    def evaluate(self, inputs):
        return self.vote(1.0, "test")


def session(day: date, start: float, step: float) -> list[Candle]:
    out, price = [], start
    for i in range(75):
        t = datetime(day.year, day.month, day.day, 9, 15, tzinfo=IST) + timedelta(minutes=5 * i)
        out.append(Candle(t, price, price + abs(step), price - abs(step), price + step, 1000))
        price += step
    return out


def make_tester():
    clock = MarketClock(SessionTimes.from_config(CFG["holding"], 15))
    builder = MarketViewBuilder([AlwaysBullish(1.0)], [], ViewThresholds(min_votes=1))
    exits = ExitPolicy(clock, 2, 1, TrailingStop(enabled=False))
    return Backtester(builder, clock, exits, OptionModel(), 30.0, 60.0, CFG["charges"])


def test_option_model_basics():
    model = OptionModel()
    assert model.atm_strike("NIFTY", 22537) == 22550 and model.atm_strike("BANKNIFTY", 55049) == 55000
    assert 0.08 <= model.sigma([100 + (i % 2) * 0.5 for i in range(200)]) <= 1.5
    call = model.price(100, 100, 10, 0.2, "CE")
    assert model.price(103, 100, 10, 0.2, "CE") > call > model.price(100, 100, 5, 0.2, "CE")  # delta and decay


def test_a_steady_rally_makes_bullish_trades_win_and_a_slide_makes_them_lose():
    days = [date(2026, 10, 5) + timedelta(days=i) for i in range(4)]
    rally = [c for i, d in enumerate(days) for c in session(d, 22000 + 300 * i, 4.0)]
    slide = [c for i, d in enumerate(days) for c in session(d, 22000 - 300 * i, -4.0)]
    up = make_tester().run("NIFTY", rally, 65)
    down = make_tester().run("NIFTY", slide, 65)
    assert up.trades and all(t.net_pnl > 0 for t in up.trades)
    assert down.trades and all(t.net_pnl < 0 for t in down.trades)
    assert len(sessions_of(rally)) == 4 and up.sessions == 3  # the first session is history only
    assert "APPROXIMATION" in format_report({"NIFTY": up}, 4)


def test_no_new_trade_within_the_re_entry_or_loss_pause():
    days = [date(2026, 10, 5) + timedelta(days=i) for i in range(4)]
    slide = [c for i, d in enumerate(days) for c in session(d, 22000 - 300 * i, -4.0)]
    result = make_tester().run("NIFTY", slide, 65)
    for previous, nxt in zip(result.trades, result.trades[1:], strict=False):
        pause = 45 if previous.net_pnl < 0 else 30
        assert (nxt.opened_at - previous.closed_at).total_seconds() >= pause * 60


def test_no_new_trade_within_the_re_entry_pause_after_a_win():
    days = [date(2026, 10, 5) + timedelta(days=i) for i in range(4)]
    rally = [c for i, d in enumerate(days) for c in session(d, 22000 + 300 * i, 4.0)]
    trades = make_tester().run("NIFTY", rally, 65).trades
    gaps = [(n.opened_at - p.closed_at).total_seconds() for p, n in zip(trades, trades[1:], strict=False)]
    assert all(p.net_pnl > 0 for p in trades) and gaps and min(gaps) >= 30 * 60


def test_decisions_never_look_ahead():
    days = [date(2026, 10, 5) + timedelta(days=i) for i in range(3)]
    base = [c for i, d in enumerate(days) for c in session(d, 22000 + 300 * i, 4.0)]
    cut = base[: 75 * 2 + 40]  # the third session stops at bar 40
    changed = cut + [Candle(c.start, c.open, c.high, c.low, c.close * 0.9, c.volume) for c in base[75 * 2 + 40 :]]
    first = make_tester().run("NIFTY", cut, 65).trades
    second = make_tester().run("NIFTY", changed, 65).trades
    opened = [t.opened_at for t in first]
    assert opened and opened == [t.opened_at for t in second][: len(opened)]  # the future did not change the past
