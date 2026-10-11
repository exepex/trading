"""Wires the live desk together from config. The only place that knows concrete classes (dependency injection)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import ROOT
from ..notify import SlackTarget
from ..providers import Provider, get_provider
from .alerts import LiveAlerts
from .contract_picker import ContractPicker, ExitLevels, PickerRules
from .exit_policy import ExitPolicy
from .feeds.nse_feed import NseLiveFeed
from .feeds.price_feed import IntradayPriceFeed, YahooPriceFeed
from .kill_switch import KillSwitch
from .market_clock import MarketClock, SessionTimes
from .market_view import MarketViewBuilder, ViewThresholds
from .paper_desk import PaperDesk
from .research.research_context import ResearchContextLoader
from .research.warehouse import ResearchWarehouse
from .results_store import ResultsStore
from .risk_gate import PortfolioGate
from .shortlist import ShortlistRules
from .signals.registry import build_guard_rules, build_signal_rules

DEFAULT_JOURNAL = ROOT / "journal" / "live_trades.json"
DEFAULT_STATE_DIR = ROOT / "data" / "live"
KILL_FLAG_NAME = "KILL"
LOCAL_RESULTS_NAME = "fno_desk.duckdb"


@dataclass
class LiveServices:
    cfg: dict
    nse_feed: NseLiveFeed
    price_feed: IntradayPriceFeed
    chain_source: Provider
    view_builder: MarketViewBuilder
    picker: ContractPicker
    gate: PortfolioGate
    desk: PaperDesk
    alerts: LiveAlerts
    store: ResultsStore
    clock: MarketClock
    kill_switch: KillSwitch
    research_loader: ResearchContextLoader
    shortlist_rules: ShortlistRules

    @property
    def live_cfg(self) -> dict:
        return self.cfg.get("live", {})


def build_live_services(
    cfg: dict, journal_path: Path = DEFAULT_JOURNAL, state_dir: Path = DEFAULT_STATE_DIR
) -> LiveServices:
    live = cfg.get("live", {})
    holding = cfg.get("holding", {})
    signals_cfg = live.get("signals", {})
    clock = MarketClock(SessionTimes.from_config(holding, signals_cfg.get("opening_range", {}).get("minutes", 15)))
    chain_source = get_provider(live.get("chain_provider", cfg.get("provider", "nse")), cfg)
    kill_switch = KillSwitch(state_dir / KILL_FLAG_NAME)
    exit_policy = ExitPolicy(
        clock,
        max_holding_days=holding.get("max_days", 2),
        exit_days_before_expiry=cfg.get("exits", {}).get("exit_days_before_expiry", 1),
    )
    return LiveServices(
        cfg=cfg,
        nse_feed=NseLiveFeed(),
        price_feed=YahooPriceFeed(),
        chain_source=chain_source,
        view_builder=MarketViewBuilder(
            build_signal_rules(signals_cfg),
            build_guard_rules(live.get("guards", {})),
            ViewThresholds.from_config(live.get("thresholds")),
        ),
        picker=ContractPicker(
            PickerRules.from_config(live.get("contract", {})),
            ExitLevels.from_config(cfg.get("exits", {}).get("long_option", {})),
            cfg.get("position_rules", {}),
        ),
        gate=PortfolioGate(cfg, kill_switch, live.get("reentry_cooldown_minutes", 30)),
        desk=PaperDesk(journal_path, cfg, chain_source, exit_policy),
        alerts=LiveAlerts(SlackTarget.from_environment(cfg)),
        store=ResultsStore(state_dir / LOCAL_RESULTS_NAME, live.get("results_database", "fno_desk")),
        clock=clock,
        kill_switch=kill_switch,
        research_loader=ResearchContextLoader(ResearchWarehouse(), live.get("news_lookback_hours", 24)),
        shortlist_rules=ShortlistRules.from_config(live.get("shortlist")),
    )
