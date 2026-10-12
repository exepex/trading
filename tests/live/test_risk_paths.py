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


def test_kill_switch_keeps_retrying_a_trade_it_cannot_price(tmp_path):
    svc, market, reference, trade = desk_with_trades(tmp_path)
    market.broken = {trade["underlying"]}
    svc.kill_switch.engage("test", at(11, 10))
    runner = LiveRunner(svc)
    runner.reference, runner.state.day = reference, at(11, 0).date()
    runner.tick(at(11, 11))
    runner.tick(at(11, 12))
    assert svc.desk.open_trades() and any("still open" in m for m in svc.alerts.messages)
    assert any("could not close" in m for m in svc.alerts.messages)  # said honestly, not "all closed"
    market.broken = set()
    runner.tick(at(11, 20))  # the next review interval: retried and closed
    assert svc.desk.open_trades() == []


def test_a_failed_morning_reference_load_is_retried(tmp_path):
    svc, _, _, _ = desk_with_trades(tmp_path)
    calls = []
    original = svc.nse_feed.lot_sizes

    def flaky():
        calls.append(1)
        if len(calls) == 1:
            raise ConnectionError("NSE down")
        return original()

    svc.nse_feed.lot_sizes = flaky
    runner = LiveRunner(svc)
    runner.tick(at(9, 0))
    assert runner.reference is None and any("reference data" in m for m in svc.alerts.messages)
    runner.tick(at(9, 2))  # too soon: not asked again
    assert len(calls) == 1
    runner.tick(at(9, 6))
    assert runner.reference is not None and runner.state.day == at(9, 6).date() and len(calls) == 2


def test_a_dead_news_watcher_is_reported_once(tmp_path):
    import threading

    svc, _, reference, _ = desk_with_trades(tmp_path)
    runner = LiveRunner(svc)
    runner.reference, runner.state.day = reference, at(11, 0).date()
    runner._news_thread = threading.Thread(target=lambda: None)
    runner._news_thread.start()
    runner._news_thread.join()
    runner.tick(at(11, 30))
    runner.tick(at(11, 45))
    assert sum("news watcher stopped" in m for m in svc.alerts.messages) == 1


def test_a_loss_closed_seconds_after_a_release_counts(tmp_path):
    cfg = load_config(overrides={"profile": "live"})
    switch = KillSwitch(tmp_path / "KILL")
    switch.release(at(10, 5) + timedelta(seconds=30))
    loss = {"status": "closed", "pnl_net": -21000, "closed_at": (at(10, 5) + timedelta(seconds=45)).isoformat()}
    assert performance_stop_reason([loss], cfg, since=switch.released_at)
    (tmp_path / "KILL.released").write_text("2026-10-12T10:05:00")  # a hand-edited time without a zone
    assert switch.released_at.utcoffset() == timedelta(hours=5, minutes=30)
