"""Wires the live desk together from config. The only place that knows concrete classes (dependency injection)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import time, timedelta
from pathlib import Path

from ..config import ROOT
from ..constants import INDEX_UNDERLYINGS
from ..http_pacing import PacedSession
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
from .learning.iv_history import IvHistory
from .market_clock import MarketClock, SessionTimes
from .market_view import MarketViewBuilder, ViewThresholds
from .move_check import MoveCheck
from .news.api_sources import api_sources_from_environment
from .news.exchange_sources import BSE_SOURCE, NSE_SOURCE, BseAnnouncementsSource, NseAnnouncementsSource
from .news.impact import ImpactSettings, NewsRoom
from .news.poll_schedule import ActiveWindow, PollSchedule, SourcePlan
from .news.rss_source import RssFeedSource
from .news.story_book import StoryBook
from .news.tagging import SymbolTagger
from .news.watcher import NewsWatcher
from .paper_desk import PaperDesk
from .research.motherduck_source import MotherDuckResearchSource
from .research.repo_source import DATASETS, RepoResearchSource
from .research.repo_sync import ResearchRepoSync
from .research.research_context import ResearchContextLoader
from .research.research_source import ResearchSource
from .results_store import JsonlResultsStore, LockedResultsStore, ResultsStore
from .risk_gate import PortfolioGate
from .shortlist import ShortlistRules
from .signals.registry import build_guard_rules, build_signal_rules

log = logging.getLogger(__name__)

DEFAULT_JOURNAL = ROOT / "journal" / "live_trades.json"
SHADOW_JOURNAL_NAME = "shadow_trades.json"  # next to the main journal: one lot of every idea, for grading
DEFAULT_STATE_DIR = ROOT / "data" / "live" / "state"  # not committed: kill flag, local databases
DEFAULT_RESULTS_DIR = ROOT / "data" / "live" / "events"  # committed: the desk's daily event log
DEFAULT_NEWS_DIR = ROOT / "data" / "live" / "news"  # committed once a day: only stories that matter to F&O
DEFAULT_RESEARCH_CLONE = ROOT / "data" / "research"  # not committed: copy of the stock tool's research files
KILL_FLAG_NAME = "KILL"
LOCAL_RESULTS_NAME = "fno_desk.duckdb"
RESEARCH_FROM_REPO = "repo"
RESEARCH_FROM_MOTHERDUCK = "motherduck"
RESULTS_TO_FILES = "files"
RESULTS_TO_DUCKDB = "duckdb"
DEFAULT_NEWS_INTERVAL_SECONDS = 120
NEWS_USER_AGENT = "Mozilla/5.0 (compatible; fno-desk/1.0; personal research)"  # honest, and accepted by the feeds
SOURCE_CONFIG_KEYS = {"NSE filings": "nse_announcements", "BSE filings": "bse_announcements"}


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
    news_room: NewsRoom | None = None  # filled by the news watcher, read by the scanner and the exit check
    iv_history: IvHistory | None = None  # daily ATM implied volatility per underlying, for IV rank

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
    store = LockedResultsStore(build_results_store(live.get("results", {}), state_dir))
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
            chain_source,
            MoveCheck(
                live.get("contract", {}).get("max_needed_to_likely_move", 1.5),
                holding.get("max_days", 2),
                cfg.get("exits", {}).get("long_option", {}).get("take_profit_pct_of_premium", 60.0),
            ),
        ),
        gate=PortfolioGate(cfg, kill_switch, live.get("reentry_cooldown_minutes", 30)),
        desk=PaperDesk(journal_path, cfg, chain_source, exit_policy),
        alerts=LiveAlerts(SlackTarget.from_environment(cfg)),
        store=store,
        clock=clock,
        kill_switch=kill_switch,
        research_loader=ResearchContextLoader(
            build_research_source(live.get("research", {})), live.get("news_lookback_hours", 24)
        ),
        shortlist_rules=ShortlistRules.from_config(live.get("shortlist")),
        news_room=build_news_room(live.get("news", {})),
        iv_history=IvHistory(store, **live.get("iv_history", {})),
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


def build_news_room(news_cfg: dict) -> NewsRoom | None:
    """Where stories live during the day. Tags by index words until company names are loaded by the watcher."""
    if not news_cfg.get("enabled"):
        return None
    book = StoryBook(
        SymbolTagger({}),
        timedelta(hours=news_cfg.get("dedupe_window_hours", 24)),
        outlet_of={feed["name"]: feed.get("outlet", feed["name"]) for feed in news_cfg.get("feeds", [])},
        primary_sources=frozenset({NSE_SOURCE, BSE_SOURCE}),
    )
    return NewsRoom(book, ImpactSettings.from_config(news_cfg.get("impact")))


def build_news_watcher(services: LiveServices) -> NewsWatcher | None:
    """The fast news watcher from `live.news`, or None when it is switched off. Makes two requests at start (the F&O
    list and company names, used to tag headlines and keep only news that matters to F&O)."""
    news_cfg = services.live_cfg.get("news", {})
    if not news_cfg.get("enabled") or services.news_room is None:
        return None
    fno_symbols, names = _fno_names(services)
    services.news_room.book.use_tagger(SymbolTagger(names))
    session = PacedSession()
    session.headers["User-Agent"] = NEWS_USER_AGENT
    source_cfg = news_cfg.get("sources", {})
    feeds = news_cfg.get("feeds", [])
    sources = [RssFeedSource(feed["name"], feed["url"], session) for feed in feeds]
    exchange_sources = {
        "nse_announcements": lambda: NseAnnouncementsSource(services.nse_feed.client),
        "bse_announcements": lambda: BseAnnouncementsSource(session),
    }
    sources += [build() for key, build in exchange_sources.items() if source_cfg.get(key, {}).get("enabled", True)]
    sources += api_sources_from_environment(session, source_cfg)
    by_name = {feed["name"]: feed for feed in feeds}
    plans = [
        _plan(source, by_name.get(source.name) or source_cfg.get(_config_key(source.name), {})) for source in sources
    ]
    window = ActiveWindow(
        time.fromisoformat(news_cfg.get("active_from", "08:45")),
        time.fromisoformat(news_cfg.get("active_until", "15:45")),
        services.clock.is_trading_day,
    )
    store = LockedResultsStore(JsonlResultsStore(Path(news_cfg.get("directory") or DEFAULT_NEWS_DIR)))
    relevant = frozenset(fno_symbols) | frozenset(INDEX_UNDERLYINGS) if fno_symbols else None
    schedule = PollSchedule(plans, news_cfg.get("min_seconds_between_requests", 5), window)
    return NewsWatcher(schedule, services.news_room, store, relevant)


def build_news_store(services: LiveServices) -> ResultsStore:
    news_cfg = services.live_cfg.get("news", {})
    return JsonlResultsStore(Path(news_cfg.get("directory") or DEFAULT_NEWS_DIR))


def _fno_names(services: LiveServices) -> tuple[set[str], dict[str, str]]:
    """F&O symbols and the company names of those in the NIFTY 500 (empty when NSE cannot be reached)."""
    try:
        fno_symbols = set(services.nse_feed.lot_sizes())
        names = services.nse_feed.company_names()
    except Exception as exc:  # noqa: BLE001 - index words and source tags still work without them
        log.warning("F&O list or company names unavailable, news tagged by index words and source tags: %s", exc)
        return set(), {}
    return fno_symbols, {s: n for s, n in names.items() if s in fno_symbols}


def _config_key(source_name: str) -> str:
    return SOURCE_CONFIG_KEYS.get(source_name, source_name.lower())


def _plan(source, opts: dict) -> SourcePlan:
    return SourcePlan(source, opts.get("every_seconds", DEFAULT_NEWS_INTERVAL_SECONDS), opts.get("daily_limit"))


def max_planned_loss(cfg: dict) -> float:
    """Rupees a single trade may lose at its stop: risk_per_trade_pct of capital."""
    capital = cfg.get("account", {}).get("capital", 0)
    return capital * cfg.get("position_rules", {}).get("risk_per_trade_pct", 2.0) / 100
