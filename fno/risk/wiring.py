"""Composition root of the risk manager (story C2): the only place that picks its concrete rules, cost model and
stressed-margin method, like `fno/storage/wiring.py` for the raw data stores. Swapping a rule or method changes this
file only."""

from __future__ import annotations

from pathlib import Path

from ..config import ROOT
from ..constants import STRESSED_MARGIN_MULTIPLIER
from ..research_engine.implied_vol import Black76
from .buckets import StructureBuckets
from .cap_settings import CapSettings, cap_settings
from .caps import BucketCap, NewRiskPerDay, OpenRiskCap, PaperAccountSize
from .drawdown import DrawdownBrake
from .manager import RiskManager
from .margins import MarginTable, MultiplierMargin, ScenarioLookupMargin, StressedMargin
from .open_risk import HeldMaxLoss, PositionRisks
from .rules import ExposureLimit, MarginRoom, MaxLossPerTrade, MaxOpenTrades, StressLoss
from .settings import RiskSettings, risk_settings
from .stress import StressEngine
from .stress_line import DailyStressLine
from .trade_costs import SimulatorTradeCosts


def build_stressed_margin(settings: RiskSettings) -> StressedMargin:
    """The one stressed-margin method frozen in `risk.stressed_margin`."""
    if settings.stressed_margin.method == STRESSED_MARGIN_MULTIPLIER:
        return MultiplierMargin(
            MarginTable(settings.margins_file, settings.margin_max_age_days), settings.stressed_margin
        )
    names = [scenario.name for scenario in settings.scenarios]
    return ScenarioLookupMargin(settings.stressed_margin, names, settings.margin_max_age_days)


def build_position_risks(cfg: dict, caps: CapSettings) -> PositionRisks:
    """Story C5: each position's bucket and B2 maximum loss."""
    costs = SimulatorTradeCosts(cfg["charges"])
    return PositionRisks(StructureBuckets(caps.bucket_sides), HeldMaxLoss(cfg["charges"]), costs)


def build_stress_line(cfg: dict) -> DailyStressLine:
    """Story C5: design 6.2's daily stress line for the card, from config.yaml `risk.stress_line`."""
    caps = cap_settings(cfg)
    return DailyStressLine(StressEngine(Black76()), build_position_risks(cfg, caps), caps.stress_line)


def build_risk_manager(cfg: dict, root: Path = ROOT) -> RiskManager:
    """Stories C2 and C5: every owner limit and risk check from config.yaml `risk`, with B2's cost model for a trade's
    money."""
    settings, costs, engine = risk_settings(cfg, root), SimulatorTradeCosts(cfg["charges"]), StressEngine(Black76())
    caps = cap_settings(cfg)
    risks, stressed = build_position_risks(cfg, caps), build_stressed_margin(settings)
    rules = (
        PaperAccountSize(caps.paper_account_rs),
        MaxLossPerTrade(costs, settings.max_loss_per_trade_rs),
        MaxOpenTrades(settings.max_open_trades),
        BucketCap(risks, caps.bucket_cap_rs),
        OpenRiskCap(risks, caps.open_risk_cap_rs),
        NewRiskPerDay(risks, caps.new_risk_per_day_rs),
        DrawdownBrake(settings.drawdown_brake_rs),
        StressLoss(engine, costs, settings.scenarios, settings.max_stress_loss_rs),
        ExposureLimit(engine, settings.exposure),
        MarginRoom(stressed, costs),
    )
    return RiskManager(rules, stressed.record(), costs)  # the same cost model prices the approved entry
