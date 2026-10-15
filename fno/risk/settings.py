"""The risk manager's settings: the `risk` block of `config.yaml` (story C2), read once and checked, never hard-coded.

Every limit, scenario and margin setting must be present and valid; a missing or malformed one is an error at start-up,
so no proposal is ever checked against a default the owner did not set.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from ..constants import STRESSED_MARGIN_METHODS, STRESSED_MARGIN_MULTIPLIER


class RiskSettingsError(ValueError):
    """The `risk` block is missing a setting, or a setting is not usable."""


@dataclass(frozen=True)
class Scenario:
    """One stress scenario: NIFTY moves by `nifty_move_pct`, every leg's implied volatility is multiplied by
    `iv_factor`, and `days` calendar days pass."""

    name: str
    nifty_move_pct: float
    iv_factor: float
    days: int = 1


@dataclass(frozen=True)
class ExposureSettings:
    """Design 8.1: account loss from a NIFTY move of `nifty_move_pct` (either way) and from a rise of `iv_rise_points`
    volatility points, each at most its limit."""

    nifty_move_pct: float
    max_move_loss_rs: float
    iv_rise_points: float
    max_iv_loss_rs: float


@dataclass(frozen=True)
class StressedMarginSettings:
    """The one frozen stressed-margin method. `multiplier` needs a factor with its source and date (expires after
    `max_age_days`); `scenario_lookup` reads a margin per scenario from `scenario_file`."""

    method: str
    multiplier: float | None
    source: str | None
    as_of: date | None
    max_age_days: int
    scenario_file: Path | None


@dataclass(frozen=True)
class RiskSettings:
    max_loss_per_trade_rs: float
    max_open_trades: int
    drawdown_brake_rs: float
    max_stress_loss_rs: float
    scenarios: tuple[Scenario, ...]
    exposure: ExposureSettings
    margins_file: Path
    margin_max_age_days: int
    stressed_margin: StressedMarginSettings


def get_setting(block: Mapping[str, Any], key: str, where: str) -> Any:
    if not isinstance(block, Mapping) or key not in block or block[key] is None:
        raise RiskSettingsError(f"config.yaml risk{where}: `{key}` is required")
    return block[key]


def positive_setting(block: Mapping[str, Any], key: str, where: str = "") -> float:
    value = get_setting(block, key, where)
    if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
        raise RiskSettingsError(f"config.yaml risk{where}: `{key}` must be a positive number, not {value!r}")
    return float(value)


def _count(block: Mapping[str, Any], key: str, where: str = "") -> int:
    value = positive_setting(block, key, where)
    if value != int(value):
        raise RiskSettingsError(f"config.yaml risk{where}: `{key}` must be a whole number, not {value!r}")
    return int(value)


def _scenario(row: Mapping[str, Any]) -> Scenario:
    move = get_setting(row, "nifty_move_pct", ".scenarios")
    if isinstance(move, bool) or not isinstance(move, int | float) or move <= -100:
        raise RiskSettingsError(f"config.yaml risk.scenarios: bad nifty_move_pct {move!r}")
    return Scenario(
        str(get_setting(row, "name", ".scenarios")),
        float(move),
        positive_setting(row, "iv_factor", ".scenarios"),
        _count(row, "days", ".scenarios"),
    )


def scenarios_at(block: Mapping[str, Any], key: str = "scenarios") -> tuple[Scenario, ...]:
    """A non-empty list of uniquely named scenarios under `key` (C2's limit scenarios, C5's stress line)."""
    rows = get_setting(block, key, "")
    if not isinstance(rows, list) or not rows:
        raise RiskSettingsError(f"config.yaml risk: `{key}` must be a non-empty list")
    scenarios = tuple(_scenario(row) for row in rows)
    names = [s.name for s in scenarios]
    if len(set(names)) != len(names):
        raise RiskSettingsError(f"config.yaml risk.{key}: names must be unique: {names}")
    return scenarios


def _exposure(block: Mapping[str, Any]) -> ExposureSettings:
    exposure = get_setting(block, "exposure", "")
    return ExposureSettings(
        *(
            positive_setting(exposure, k, ".exposure")
            for k in ("nifty_move_pct", "max_move_loss_rs", "iv_rise_points", "max_iv_loss_rs")
        )
    )


def _optional_date(value: Any) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _stressed_margin(block: Mapping[str, Any], root: Path) -> StressedMarginSettings:
    """Only the method and its expiry are required here: a missing factor, source or file fails closed when a
    proposal is checked (MarginRoom), so the desk refuses trades instead of refusing to start."""
    stressed = get_setting(block, "stressed_margin", "")
    method = get_setting(stressed, "method", ".stressed_margin")
    if method not in STRESSED_MARGIN_METHODS:
        raise RiskSettingsError(f"config.yaml risk.stressed_margin: method must be one of {STRESSED_MARGIN_METHODS}")
    factor = stressed.get("multiplier")
    if factor is not None and (isinstance(factor, bool) or not isinstance(factor, int | float) or factor < 1):
        raise RiskSettingsError(f"config.yaml risk.stressed_margin: multiplier must be at least 1, not {factor!r}")
    scenario_file = stressed.get("scenario_file")
    return StressedMarginSettings(
        method,
        float(factor) if factor is not None else None,
        stressed.get("source") or None,
        _optional_date(stressed.get("as_of")),
        _count(stressed, "max_age_days", ".stressed_margin"),
        root / scenario_file if scenario_file else None,
    )


def risk_settings(config: Mapping[str, Any], root: Path) -> RiskSettings:
    """The checked `risk` block of an app config (`fno.config.load_app_config`); file paths are relative to `root`."""
    block = get_setting(config, "risk", "")
    margins = get_setting(block, "margins", "")
    settings = RiskSettings(
        positive_setting(block, "max_loss_per_trade_rs"),
        _count(block, "max_open_trades"),
        positive_setting(block, "drawdown_brake_rs"),
        positive_setting(block, "max_stress_loss_rs"),
        scenarios_at(block),
        _exposure(block),
        root / str(get_setting(margins, "file", ".margins")),
        _count(margins, "max_age_days", ".margins"),
        _stressed_margin(block, root),
    )
    if settings.stressed_margin.method == STRESSED_MARGIN_MULTIPLIER and settings.stressed_margin.scenario_file:
        raise RiskSettingsError("config.yaml risk.stressed_margin: scenario_file belongs to scenario_lookup only")
    return settings
