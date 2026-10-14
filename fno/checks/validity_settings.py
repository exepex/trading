"""The owner's limits as C4 reads them (story C4, judge 83): straight from `config.yaml` `risk` and `risk_free_rate`,
not through the risk manager's settings code. C2 checks the block's shape at start-up, so a malformed value never
reaches here. A missing stressed-margin factor, source or date is not an error here: the margin check fails closed."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Shock:
    name: str
    move_pct: float
    sigma_factor: float = 1.0
    sigma_add: float = 0.0  # volatility points as a fraction (5 points = 0.05)
    days: int = 0


@dataclass(frozen=True)
class MarginSettings:
    file: Path
    max_age_days: int
    method: str
    multiplier: float | None
    source: str | None
    as_of: date | None
    multiplier_max_age_days: int


@dataclass(frozen=True)
class ValidityLimits:
    max_loss_per_trade: float
    max_open_trades: int
    drawdown_brake: float
    max_stress_loss: float
    scenarios: tuple[Shock, ...]
    exposure_moves: tuple[Shock, Shock]  # NIFTY up and down by the exposure move, no time passing
    exposure_iv: Shock  # implied volatility up by the exposure points
    max_move_loss: float
    max_iv_loss: float
    margins: MarginSettings
    rate: float


def _date(value) -> date | None:
    return value if value is None or isinstance(value, date) else date.fromisoformat(str(value))


def _margins(block: Mapping, root: Path) -> MarginSettings:
    files, stressed = block["margins"], block["stressed_margin"]
    factor = stressed.get("multiplier")
    return MarginSettings(
        root / str(files["file"]), int(files["max_age_days"]), str(stressed["method"]),
        None if factor is None else float(factor), stressed.get("source") or None, _date(stressed.get("as_of")),
        int(stressed["max_age_days"]),
    )  # fmt: skip


def limits_from_config(cfg: Mapping, root: Path) -> ValidityLimits:
    risk, exposure = cfg["risk"], cfg["risk"]["exposure"]
    move, points = float(exposure["nifty_move_pct"]), float(exposure["iv_rise_points"])
    scenarios = tuple(
        Shock(s["name"], float(s["nifty_move_pct"]), float(s["iv_factor"]), 0.0, int(s["days"]))
        for s in risk["scenarios"]
    )
    return ValidityLimits(
        float(risk["max_loss_per_trade_rs"]), int(risk["max_open_trades"]), float(risk["drawdown_brake_rs"]),
        float(risk["max_stress_loss_rs"]), scenarios,
        (Shock(f"nifty_up_{move:g}pct", move), Shock(f"nifty_down_{move:g}pct", -move)),
        Shock(f"iv_up_{points:g}points", 0.0, 1.0, points / 100), float(exposure["max_move_loss_rs"]),
        float(exposure["max_iv_loss_rs"]), _margins(risk, root), float(cfg["risk_free_rate"]),
    )  # fmt: skip
