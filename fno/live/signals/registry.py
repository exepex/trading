"""Builds the active rules and guards from config.yaml `live.signals` / `live.guards`."""

from __future__ import annotations

from .base import GuardRule, SignalRule
from .guards import BanListGuard, EarningsGuard, ExpensiveOptionsGuard, MarketStressGuard
from .market_signals import GlobalCues, MarketBreadth, SectorStrength, VixDirection
from .news_signals import FastNews, NewsShockGuard
from .option_signals import OptionWritingPressure
from .positioning import FuturesOiBuildup
from .price_action import IntradayTrend, OpeningRangeBreakout, RelativeStrength, VwapPosition
from .research_signals import AnnouncementCatalyst, BlockDealFlow, ForeignFlow, ModelScore, NewsSentiment
from .session_levels import PreviousDayLevels, VolumeConfirmation

SIGNAL_RULES: dict[str, type[SignalRule]] = {
    rule.name: rule
    for rule in (
        OpeningRangeBreakout,
        VwapPosition,
        IntradayTrend,
        RelativeStrength,
        PreviousDayLevels,
        VolumeConfirmation,
        FuturesOiBuildup,
        OptionWritingPressure,
        SectorStrength,
        MarketBreadth,
        GlobalCues,
        VixDirection,
        NewsSentiment,
        ModelScore,
        AnnouncementCatalyst,
        BlockDealFlow,
        ForeignFlow,
        FastNews,
    )
}
GUARD_RULES: dict[str, type[GuardRule]] = {
    guard.name: guard
    for guard in (BanListGuard, EarningsGuard, MarketStressGuard, ExpensiveOptionsGuard, NewsShockGuard)
}


def build_signal_rules(signals_cfg: dict) -> list[SignalRule]:
    """Each entry: {weight: float, enabled: bool, ...rule settings}."""
    rules = []
    for name, settings in signals_cfg.items():
        if name not in SIGNAL_RULES:
            raise ValueError(f"Unknown signal rule '{name}'. Known: {', '.join(sorted(SIGNAL_RULES))}")
        settings = dict(settings or {})
        if settings.pop("enabled", True):
            rules.append(SIGNAL_RULES[name](settings.pop("weight", 1.0), settings))
    return rules


def build_guard_rules(guards_cfg: dict) -> list[GuardRule]:
    guards = []
    for name, settings in guards_cfg.items():
        if name not in GUARD_RULES:
            raise ValueError(f"Unknown guard '{name}'. Known: {', '.join(sorted(GUARD_RULES))}")
        settings = dict(settings or {})
        if settings.pop("enabled", True):
            guards.append(GUARD_RULES[name](settings))
    return guards
