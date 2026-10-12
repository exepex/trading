"""Wires the live desk together from config. The only place that knows concrete classes (dependency injection)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import ROOT
from ..notify import SlackTarget
from ..providers import Provider, get_provider
from ..providers.cached import CachedProvider
from .alerts import LiveAlerts
from .contract_picker import ContractPicker, ExitLevels, PickerRules
from .duckdb_results_store import DuckDbResultsStore
from .exit_policy import ExitPolicy, TrailingStop
from .feeds.nse_feed import NseLiveFeed
from .feeds.price_feed import IntradayPriceFeed, YahooPriceFeed
from .kill_switch import KillSwitch
from .market_clock import MarketClock, SessionTimes
from .market_view import MarketViewBuilder, ViewThresholds
from .paper_desk import PaperDesk
from .research.motherduck_source import MotherDuckResearchSource
from .research.repo_source import DATASETS, RepoResearchSource
from .research.repo_sync import ResearchRepoSync
from .research.research_context import ResearchContextLoader
from .research.research_source import ResearchSource
from .results_store import JsonlResultsStore, ResultsStore
from .risk_gate import PortfolioGate
from .shortlist import ShortlistRules
from .signals.registry import build_guard_rules, build_signal_rules

DEFAULT_JOURNAL = ROOT / "journal" / "live_trades.json"
SHADOW_JOURNAL_NAME = "shadow_trades.json"  # next to the main journal: one lot of every idea, for grading
DEFAULT_STATE_DIR = ROOT / "data" / "live" / "state"  # not committed: kill flag, local databases
DEFAULT_RESULTS_DIR = ROOT / "data" / "live" / "events"  # committed: the desk's daily event log
DEFAULT_RESEARCH_CLONE = ROOT / "data" / "research"  # not committed: copy of the stock tool's research files
KILL_FLAG_NAME = "KILL"
LOCAL_RESULTS_NAME = "fno_desk.duckdb"
RESEARCH_FROM_REPO = "repo"
RESEARCH_FROM_MOTHERDUCK = "motherduck"
RESULTS_TO_FILES = "files"
RESULTS_TO_DUCKDB = "duckdb"


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
    shadow_desk: PaperDesk | None = None

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
    chain_source = CachedProvider(get_provider(live.get("chain_provider", cfg.get("provider", "nse")), cfg))
    kill_switch = KillSwitch(state_dir / KILL_FLAG_NAME)
    exit_policy = ExitPolicy(
        clock,
        max_holding_days=holding.get("max_days", 2),
        exit_days_before_expiry=cfg.get("exits", {}).get("exit_days_before_expiry", 1),
        trailing=TrailingStop.from_config(cfg.get("exits", {}).get("trailing_stop", {})),
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
            max_planned_loss(cfg),
        ),
        gate=PortfolioGate(cfg, kill_switch, live.get("reentry_cooldown_minutes", 30)),
        desk=PaperDesk(journal_path, cfg, chain_source, exit_policy),
        alerts=LiveAlerts(SlackTarget.from_environment(cfg)),
        store=build_results_store(live.get("results", {}), state_dir),
        clock=clock,
        kill_switch=kill_switch,
        research_loader=ResearchContextLoader(
            build_research_source(live.get("research", {})), live.get("news_lookback_hours", 24)
        ),
        shortlist_rules=ShortlistRules.from_config(live.get("shortlist")),
        shadow_desk=(
            PaperDesk(journal_path.with_name(SHADOW_JOURNAL_NAME), cfg, chain_source, exit_policy, enforce_limits=False)
            if live.get("shadow_book", {}).get("enabled")
            else None
        ),
    )


def build_research_source(research_cfg: dict) -> ResearchSource:
    """The stock tool's research: its GitHub data files by default, its MotherDuck copy as an option."""
    market = research_cfg.get("market", "india")
    if research_cfg.get("source", RESEARCH_FROM_REPO) == RESEARCH_FROM_MOTHERDUCK:
        return MotherDuckResearchSource(market)
    clone = Path(research_cfg.get("local_path") or DEFAULT_RESEARCH_CLONE)
    folders = [f"data/{market}/{dataset}" for dataset in DATASETS]
    sync = ResearchRepoSync(research_cfg["repo_url"], clone, folders) if research_cfg.get("repo_url") else None
    return RepoResearchSource(clone / "data" / market, sync)


def build_results_store(results_cfg: dict, state_dir: Path) -> ResultsStore:
    """Daily JSONL files saved to GitHub by default; DuckDB/MotherDuck as an option."""
    if results_cfg.get("store", RESULTS_TO_FILES) == RESULTS_TO_DUCKDB:
        return DuckDbResultsStore(state_dir / LOCAL_RESULTS_NAME, results_cfg.get("database", "fno_desk"))
    return JsonlResultsStore(Path(results_cfg.get("directory") or DEFAULT_RESULTS_DIR))


def max_planned_loss(cfg: dict) -> float:
    """Rupees a single trade may lose at its stop: risk_per_trade_pct of capital."""
    capital = cfg.get("account", {}).get("capital", 0)
    return capital * cfg.get("position_rules", {}).get("risk_per_trade_pct", 2.0) / 100
