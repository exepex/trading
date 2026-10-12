"""Risk controls must still act when one piece of data fails (judge, wave 0 findings 1, 2, 8, 9)."""

from datetime import timedelta

from fno.config import load_config
from fno.constants import ExitReason, SessionPhase
from fno.live.kill_switch import KillSwitch
from fno.live.learning.performance import current_drawdown, performance_stop_reason
from fno.live.news.models import NewsItem
from fno.live.research.research_context import ResearchSnapshot
from fno.live.runner import LiveRunner
from fno.live.scanner import LiveScanner
from fno.live.universe import ReferenceData

from .fakes import at
from .test_desk_end_to_end import LOTS, ShiftableSample, services


class BrokenChains(ShiftableSample):
    """Chains fail for the named underlyings (network, NSE refusing)."""

    broken: set = set()

    def chain(self, underlying, expiry):
        if underlying in self.broken:
            raise ConnectionError(f"{underlying} chain unavailable")
        return super().chain(underlying, expiry)


def desk_with_trades(tmp_path):
    cfg = load_config()
    market = BrokenChains(cfg, as_of=at(11, 0))
    svc = services(tmp_path, market)
    reference = ReferenceData(loaded_on=at(11, 0).date(), lot_sizes=LOTS)
    LiveScanner(svc).run_cycle(at(11, 0), SessionPhase.TRADING, reference, ResearchSnapshot())
    trade = svc.desk.open_trades()[0]
    return svc, market, reference, trade


def test_square_off_trim_with_a_broken_chain_still_saves_the_other_exits(tmp_path):
    svc, market, _, trade = desk_with_trades(tmp_path)
    svc.desk.cfg = dict(svc.desk.cfg, account={**svc.desk.cfg["account"], "max_overnight_premium": 0})
    market.broken = {trade["underlying"]}
    closed, errors = svc.desk.review_open_trades(at(15, 16), SessionPhase.SQUARE_OFF)
    assert closed == [] and errors  # the broken trade is reported, the review does not crash
    market.broken = set()
    closed, _ = svc.desk.review_open_trades(at(15, 17), SessionPhase.SQUARE_OFF)
    assert [t["exit_reason"] for t in closed] == [ExitReason.OVERNIGHT_LIMIT.value]


def test_a_failing_news_exit_never_loses_exits_already_made(tmp_path):
    svc, market, reference, trade = desk_with_trades(tmp_path)
    market.spot_shift_pct = 3.0  # the review closes the trade at its target

    def news_exit_bug(*_args, **_kwargs):
        raise RuntimeError("news exit failed")

    svc.news_exit.close_hit = news_exit_bug
    engaged = []
    runner = LiveRunner(svc)
    runner._stop_if_performance_breaks = lambda now: engaged.append(now)
    runner.reference, runner.state.day = reference, at(11, 0).date()
    runner.tick(at(11, 30))
    assert svc.store.count("closed") == 1 and any("PAPER EXIT" in m for m in svc.alerts.messages)
    assert engaged  # the automatic kill-switch check still ran


def test_one_trade_that_cannot_be_closed_does_not_stop_the_news_exit(tmp_path):
    svc, _, _, trade = desk_with_trades(tmp_path)
    shock = NewsItem("NSE filings", "NIFTY: SEBI bans derivatives trading, markets plunge", symbols=("NIFTY",))
    svc.news_room.book.add(shock, at(11, 5))

    def broken_close(*_args, **_kwargs):
        raise ConnectionError("chain unavailable")

    svc.desk.close = broken_close
    closed, errors = svc.news_exit.close_hit(svc.desk, at(11, 6))
    assert closed == [] and errors and trade["id"] in errors[0]


def test_the_automatic_stop_judges_the_current_drawdown_and_restarts_after_a_review(tmp_path):
    cfg = load_config(overrides={"profile": "live"})

    def closed(pnl, minute):
        stamp = (at(10, 0) + timedelta(minutes=minute)).isoformat()
        return {"status": "closed", "pnl_net": pnl, "closed_at": stamp, "opened_at": stamp}

    deep = [closed(-21000, 0)]
    assert "below the best point" in performance_stop_reason(deep, cfg)
    recovered = deep + [closed(1000, i + 1) for i in range(25)]
    assert current_drawdown([t["pnl_net"] for t in recovered]) == 0
    assert performance_stop_reason(recovered, cfg) is None
    switch = KillSwitch(tmp_path / "KILL")
    switch.engage("automatic", at(10, 1))
    switch.release(at(10, 2))
    assert not switch.engaged and switch.released_at == at(10, 2)
    assert performance_stop_reason(deep, cfg, since=switch.released_at) is None  # reviewed history is not re-judged


def test_the_shadow_book_ignores_the_overnight_cap_and_follows_the_news_exit(tmp_path):
    svc, market, reference, _ = desk_with_trades(tmp_path)
    assert svc.shadow_desk.open_trades()
    svc.shadow_desk.cfg = dict(
        svc.shadow_desk.cfg, account={**svc.shadow_desk.cfg["account"], "max_overnight_premium": 0}
    )
    closed, _ = svc.shadow_desk.review_open_trades(at(15, 16), SessionPhase.SQUARE_OFF)
    assert closed == []  # no portfolio trim for the shadow book
    shock = NewsItem("NSE filings", "NIFTY: SEBI bans derivatives trading, markets plunge", symbols=("NIFTY",))
    svc.news_room.book.add(shock, at(11, 5))
    shadow_closed, _ = svc.news_exit.close_hit(svc.shadow_desk, at(11, 6))
    assert [t["exit_reason"] for t in shadow_closed] == [ExitReason.ADVERSE_NEWS.value]
