from dataclasses import replace
from datetime import date
from pathlib import Path

from fno.config import load_config
from fno.constants import ExitReason, SessionPhase
from fno.live.feeds.nse_feed import OpenInterestMove
from fno.live.feeds.price_feed import DayQuote
from fno.live.news.models import NewsItem
from fno.live.research.research_context import ResearchSnapshot
from fno.live.results_store import JsonlResultsStore
from fno.live.runner import LiveRunner
from fno.live.scanner import LiveScanner
from fno.live.services import build_live_services
from fno.live.universe import ReferenceData
from fno.providers.sample import SampleProvider

from .fakes import CapturingAlerts, FakeNseFeed, FakePriceFeed, at, trending_candles

LOTS = {"NIFTY": 65, "BANKNIFTY": 30}


class ShiftableSample(SampleProvider):
    """Sample chains whose spot can be moved between calls, to simulate the market."""

    def expiries(self, underlying):
        return [date(2026, 10, 13), date(2026, 10, 20), date(2026, 10, 27)]


def services(tmp_path: Path, chain_source):
    cfg = load_config(overrides={"live": {"always_scan": [], "shortlist": {"min_traded_value": 0}}})
    base = build_live_services(cfg, journal_path=tmp_path / "live.json", state_dir=tmp_path)
    price_feed = FakePriceFeed(
        {"NIFTY": DayQuote("NIFTY", 22950.0, 22500.0), "BANKNIFTY": DayQuote("BANKNIFTY", 55000.0, 55000.0)},
        {"NIFTY": trending_candles(22500, 0.12, 30)},
    )
    nse = FakeNseFeed({"NIFTY": OpenInterestMove("NIFTY", 9.0, 22950.0, 1e10)}, LOTS)
    base.desk.chain_source = chain_source
    base.shadow_desk.chain_source = chain_source
    return replace(
        base,
        price_feed=price_feed,
        nse_feed=nse,
        chain_source=chain_source,
        alerts=CapturingAlerts(),
        store=JsonlResultsStore(tmp_path / "events"),
        research_loader=StubResearchLoader(),
    )


class StubResearchLoader:
    def load(self, now, news_since=None):
        return ResearchSnapshot(loaded_at=now)


def test_scan_opens_a_paper_trade_and_runner_exits_on_target(tmp_path):
    cfg = load_config()
    market = ShiftableSample(cfg, as_of=at(11, 0))
    svc = services(tmp_path, market)
    reference = ReferenceData(loaded_on=at(11, 0).date(), lot_sizes=LOTS)
    report = LiveScanner(svc).run_cycle(at(11, 0), SessionPhase.TRADING, reference, ResearchSnapshot())

    assert report.shortlisted == ["NIFTY"]  # BANKNIFTY did not move enough
    assert len(report.opened) == 1, report.rejected
    trade = svc.desk.open_trades()[0]
    assert trade["contract_name"].startswith("NIFTY 20 Oct") and trade["contract_name"].endswith("Call")
    assert "PAPER BUY" in svc.alerts.messages[0]
    assert svc.store.count("opened") == 1

    # The market rallies 3%: the next review closes the call at its target, net of charges.
    market.spot_shift_pct = 3.0
    runner = LiveRunner(svc)
    runner.reference, runner.state.day = reference, at(11, 0).date()
    runner.tick(at(11, 30))
    closed = [t for t in svc.desk.trades() if t["status"] == "closed"]
    assert closed and closed[0]["exit_reason"] == ExitReason.TARGET.value
    assert closed[0]["pnl_net"] == round(closed[0]["pnl_gross"] - closed[0]["charges"], 2)
    assert any("PAPER EXIT" in m for m in svc.alerts.messages)

    # The shadow book tracked the same idea at one lot and closed it on the same rule, without alerts.
    first = svc.shadow_desk.trades()[0]
    assert first["candidate"] == trade["candidate"] and first["lots"] == 1
    assert first["exit_reason"] == ExitReason.TARGET.value
    assert svc.store.count("shadow_closed") == 1
    assert not any("shadow" in m.lower() for m in svc.alerts.messages)


def test_shadow_book_takes_each_contract_once_a_day(tmp_path):
    cfg = load_config()
    market = ShiftableSample(cfg, as_of=at(11, 0))
    svc = services(tmp_path, market)
    reference = ReferenceData(loaded_on=at(11, 0).date(), lot_sizes=LOTS)
    for minute in (0, 3, 6):
        LiveScanner(svc).run_cycle(at(11, minute), SessionPhase.TRADING, reference, ResearchSnapshot())
    assert len(svc.shadow_desk.trades()) == 1


def test_kill_switch_closes_everything_once(tmp_path):
    cfg = load_config()
    market = ShiftableSample(cfg, as_of=at(11, 0))
    svc = services(tmp_path, market)
    reference = ReferenceData(loaded_on=at(11, 0).date(), lot_sizes=LOTS)
    LiveScanner(svc).run_cycle(at(11, 0), SessionPhase.TRADING, reference, ResearchSnapshot())
    assert svc.desk.open_trades()

    svc.kill_switch.engage("test", at(11, 5))
    runner = LiveRunner(svc)
    runner.reference, runner.state.day = reference, at(11, 0).date()
    runner.tick(at(11, 6))
    runner.tick(at(11, 7))
    assert not svc.desk.open_trades()
    assert svc.alerts.messages.count("kill switch") == 1


def test_strong_credible_news_against_an_open_trade_closes_it_early(tmp_path):
    cfg = load_config()
    market = ShiftableSample(cfg, as_of=at(11, 0))
    svc = services(tmp_path, market)
    reference = ReferenceData(loaded_on=at(11, 0).date(), lot_sizes=LOTS)
    LiveScanner(svc).run_cycle(at(11, 0), SessionPhase.TRADING, reference, ResearchSnapshot())
    trade = svc.desk.open_trades()[0]
    assert trade["direction"] == "bullish"
    shock = NewsItem("NSE filings", "NIFTY: SEBI bans derivatives trading, markets plunge", symbols=("NIFTY",))
    svc.news_room.book.add(shock, at(11, 5))
    runner = LiveRunner(svc)
    runner.reference, runner.state.day = reference, at(11, 0).date()
    runner.tick(at(11, 6))
    closed = [t for t in svc.desk.trades() if t["id"] == trade["id"]][0]
    assert closed["exit_reason"] == ExitReason.ADVERSE_NEWS.value and "regulatory" in closed["exit_note"]
