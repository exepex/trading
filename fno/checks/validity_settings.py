"""The owner's limits as C4 reads them (stories C4 and C5, judge 83): straight from `config.yaml` `risk` (one profile
of `risk.profiles`) and `risk_free_rate`, not through the risk manager's settings code. C2 checks the block's shape at
start-up, so a malformed value never reaches here. A missing stressed-margin factor, source or date is not an error
here: the margin check fails closed. C4 runs a limit only when the profile lists its rule, as C2 does."""

from __future__ import annotations

from collections.abc import Callable, Mapping
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
    max_age_days: int | None  # the Manual profile: calendar days
    max_age_sessions: int | None  # the books (design 6.1a): sessions, counted with `previous_session`
    method: str
    multiplier: float | None
    source: str | None
    as_of: date | None
    multiplier_max_age_days: int
    previous_session: Callable[[date], date] | None = None  # NSE's session calendar (A7)

    def fresh(self, as_of: date, day: date) -> bool:
        if self.max_age_sessions is None:
            return (day - as_of).days <= self.max_age_days
        if self.previous_session is None:
            return False  # no calendar: fail closed
        oldest = day
        try:
            for _ in range(self.max_age_sessions):
                oldest = self.previous_session(oldest)
        except ValueError:  # the calendar cannot answer for that day: fail closed
            return False
        return as_of >= oldest


@dataclass(frozen=True)
class CapLimits:
    """Story C5's caps as C4 reads them: sums of maximum losses, the proposal's included."""

    bucket: float | None  # None: the profile does not run that cap
    open_risk: float | None
    new_risk_per_day: float | None
    sides: Mapping[str, object]  # structure code -> its side, or a list of sides (a directional spread)


@dataclass(frozen=True)
class ValidityLimits:
    rules: tuple[str, ...]  # the profile's rules: C4 recomputes exactly these
    paper_account: float
    max_loss_per_trade: float
    drawdown_brake: float
    scenarios: tuple[Shock, ...]
    margins: MarginSettings
    rate: float
    max_open_trades: int | None = None
    max_stress_loss: float | None = None
    exposure_moves: tuple[Shock, Shock] | None = None  # NIFTY up and down by the exposure move, no time passing
    exposure_iv: Shock | None = None  # implied volatility up by the exposure points
    max_move_loss: float | None = None
    max_iv_loss: float | None = None
    caps: CapLimits | None = None


def _date(value) -> date | None:
    return value if value is None or isinstance(value, date) else date.fromisoformat(str(value))


def _margins(risk: Mapping, profile: Mapping, root: Path, previous_session) -> MarginSettings:
    files, stressed = risk["margins"], risk["stressed_margin"]
    factor, days = stressed.get("multiplier"), profile.get("margin_max_age_days")
    sessions = profile.get("margin_max_age_sessions")
    return MarginSettings(
        root / str(files["file"]), None if days is None else int(days), None if sessions is None else int(sessions),
        str(stressed["method"]), None if factor is None else float(factor), stressed.get("source") or None,
        _date(stressed.get("as_of")), int(stressed["max_age_days"]), previous_session,
    )  # fmt: skip


def _exposure(profile: Mapping) -> dict:
    exposure = profile["exposure"]
    move, points = float(exposure["nifty_move_pct"]), float(exposure["iv_rise_points"])
    return {
        "exposure_moves": (Shock(f"nifty_up_{move:g}pct", move), Shock(f"nifty_down_{move:g}pct", -move)),
        "exposure_iv": Shock(f"iv_up_{points:g}points", 0.0, 1.0, points / 100),
        "max_move_loss": float(exposure["max_move_loss_rs"]),
        "max_iv_loss": float(exposure["max_iv_loss_rs"]),
    }


def _optional(profile: Mapping, rules: tuple[str, ...]) -> dict:
    values: dict = {}
    if "max_open_trades" in rules:
        values["max_open_trades"] = int(profile["max_open_trades"])
    if "stress_loss" in rules:
        values["max_stress_loss"] = float(profile["max_stress_loss_rs"])
    if "exposure_limit" in rules:
        values |= _exposure(profile)
    if "bucket_sides" in profile:
        amounts = (profile.get(k) for k in ("bucket_cap_rs", "open_risk_cap_rs", "new_risk_per_day_rs"))
        values["caps"] = CapLimits(*(None if a is None else float(a) for a in amounts), dict(profile["bucket_sides"]))
    return values


class ValidityLimitsError(ValueError):
    """A setting a listed rule needs is missing: C4 refuses to start rather than check with a gap."""


NEEDS = {
    "max_open_trades": ("max_open_trades",), "stress_loss": ("max_stress_loss_rs",), "exposure_limit": ("exposure",),
    "bucket_cap": ("bucket_cap_rs", "bucket_sides"), "open_risk_cap": ("open_risk_cap_rs", "bucket_sides"),
    "new_risk_per_day": ("new_risk_per_day_rs", "bucket_sides"),
}  # fmt: skip
ALWAYS = ("paper_account_rs", "max_loss_per_trade_rs", "drawdown_brake_rs")


def _require(profile: Mapping, rules: tuple[str, ...], name: str) -> None:
    needed = set(ALWAYS) | {key for rule in rules for key in NEEDS.get(rule, ())}
    missing = sorted(key for key in needed if profile.get(key) is None)
    ages = [key for key in ("margin_max_age_days", "margin_max_age_sessions") if profile.get(key) is not None]
    if missing or len(ages) != 1:
        raise ValidityLimitsError(f"risk.profiles.{name}: missing {missing}, margin ages set {ages} (need exactly one)")


def limits_from_config(cfg: Mapping, root: Path, profile_name: str, previous_session=None) -> ValidityLimits:
    """Risk profile `profile_name`'s limits; `previous_session` is NSE's calendar step for a margin age in sessions."""
    risk = cfg["risk"]
    profile = risk["profiles"][profile_name]
    rules = tuple(profile["rules"])
    _require(profile, rules, profile_name)
    scenarios = tuple(
        Shock(s["name"], float(s["nifty_move_pct"]), float(s["iv_factor"]), 0.0, int(s["days"]))
        for s in risk["scenarios"]
    )
    return ValidityLimits(
        rules, float(profile["paper_account_rs"]), float(profile["max_loss_per_trade_rs"]),
        float(profile["drawdown_brake_rs"]), scenarios, _margins(risk, profile, root, previous_session),
        float(cfg["risk_free_rate"]), **_optional(profile, rules),
    )  # fmt: skip
