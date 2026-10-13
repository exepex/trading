"""Composition root of the risk manager (story C2): the only place that picks its concrete rules, cost model and
stressed-margin method, like `fno/storage/wiring.py` for the raw data stores. Swapping a rule or method changes this
file only."""

from __future__ import annotations

from pathlib import Path

from ..config import ROOT
from ..constants import STRESSED_MARGIN_MULTIPLIER
from ..research_engine.implied_vol import Black76
from .drawdown import DrawdownBrake
from .manager import RiskManager
from .margins import MarginTable, MultiplierMargin, ScenarioLookupMargin, StressedMargin
from .rules import ExposureLimit, MarginRoom, MaxLossPerTrade, MaxOpenTrades, StressLoss
from .settings import RiskSettings, risk_settings
from .stress import StressEngine
from .trade_costs import SimulatorTradeCosts


def build_stressed_margin(settings: RiskSettings) -> StressedMargin:
    """The one stressed-margin method frozen in `risk.stressed_margin`."""
    if settings.stressed_margin.method == STRESSED_MARGIN_MULTIPLIER:
        return MultiplierMargin(
            MarginTable(settings.margins_file, settings.margin_max_age_days), settings.stressed_margin
        )
    names = [scenario.name for scenario in settings.scenarios]
    return ScenarioLookupMargin(settings.stressed_margin, names, settings.margin_max_age_days)


def build_risk_manager(cfg: dict, root: Path = ROOT) -> RiskManager:
    """Story C2: every owner limit and risk check from config.yaml `risk`, with B2's cost model for a trade's money."""
    settings, costs, engine = risk_settings(cfg, root), SimulatorTradeCosts(cfg["charges"]), StressEngine(Black76())
    stressed = build_stressed_margin(settings)
    rules = (
        MaxLossPerTrade(costs, settings.max_loss_per_trade_rs),
        MaxOpenTrades(settings.max_open_trades),
        DrawdownBrake(settings.drawdown_brake_rs),
        StressLoss(engine, costs, settings.scenarios, settings.max_stress_loss_rs),
        ExposureLimit(engine, settings.exposure),
        MarginRoom(stressed, costs),
    )
    return RiskManager(rules, stressed.record())
