"""The AI minutes cap for books and roles (story BG1; owner decision of 15 Oct 2026: half of the plan's measured session
minutes, alert at 80%, AI roles stop at 100%). The plan publishes no minutes allowance, so by default the basis is all
measured session minutes of the month (every purpose); the owner may set their own monthly figure instead."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..constants import BUDGET_ALERT, BUDGET_OK, BUDGET_STOP, BUDGET_UNKNOWN, PURPOSE_BOOKS_AND_ROLES

BASIS_MEASURED = "measured: all recorded session minutes of the month (books, roles, development, data routines)"
BASIS_OWNER = "owner's figure: {minutes:,.0f} plan minutes a month (config.yaml budget.plan_minutes_per_month)"
NOTHING_MEASURED = "unknown: no minutes to measure against"
NO_DEVELOPMENT = (
    "unknown: no minutes other than the books' and roles' are recorded, so the measured basis would count them as all "
    "the use"
)
NOT_CAPTURED = "unknown: {n} fired AI book session(s) not captured, so the true share may be above the alert level"
LOWER_BOUND = "at least this level: {n} fired AI book session(s) not captured would only raise the share"
MEASURED_LIMIT = (
    "limit: the plan's real capacity is not measurable (its rate-limit data gives no minutes), so this basis moves "
    "with development: quiet development raises the books' share, busy development loosens the cap"
)


@dataclass(frozen=True)
class CapSettings:
    share_pct: Decimal  # of the basis, for books and roles
    alert_pct: Decimal
    stop_pct: Decimal
    plan_minutes: Decimal | None  # the owner's own monthly figure, if set

    @classmethod
    def from_config(cls, budget: dict) -> CapSettings:
        plan = budget.get("plan_minutes_per_month")
        return cls(_dec(budget["books_and_roles_share_pct"]), _dec(budget["alert_pct"]), _dec(budget["stop_pct"]),
                   _dec(plan) if plan is not None else None)  # fmt: skip


@dataclass(frozen=True)
class CapReading:
    books_and_roles_minutes: float
    basis_minutes: float
    cap_minutes: float
    pct_of_cap: float | None  # None: nothing to measure against
    level: str
    basis: str
    note: str = ""  # why the level is unknown, or why it is a lower bound


def cap_reading(usage_rows: list[dict], settings: CapSettings, missing_captures: int = 0) -> CapReading:
    """Exact in decimals, so a share of exactly 80% or 100% is never read as just below it."""
    used = sum((_dec(r["minutes"]) for r in usage_rows if r["purpose"] == PURPOSE_BOOKS_AND_ROLES), Decimal(0))
    if settings.plan_minutes is not None:
        basis_minutes, basis = _dec(settings.plan_minutes), BASIS_OWNER.format(minutes=_dec(settings.plan_minutes))
    else:
        basis_minutes, basis = sum((_dec(r["minutes"]) for r in usage_rows), Decimal(0)), BASIS_MEASURED
    cap = basis_minutes * _dec(settings.share_pct) / 100
    level, note = _level(used, cap, settings), ""
    if level == BUDGET_UNKNOWN:
        note = NOTHING_MEASURED + (
            f"; {missing_captures} fired AI book session(s) not captured" if missing_captures else ""
        )
    elif settings.plan_minutes is None and basis_minutes == used:
        level, note = BUDGET_UNKNOWN, NO_DEVELOPMENT
    elif missing_captures and level == BUDGET_OK:
        level, note = BUDGET_UNKNOWN, NOT_CAPTURED.format(n=missing_captures)
    elif missing_captures:
        note = LOWER_BOUND.format(n=missing_captures)
    pct = float(100 * used / cap) if cap > 0 else None
    return CapReading(float(used), float(basis_minutes), float(cap), pct, level, basis, note)


def _level(used: Decimal, cap: Decimal, settings: CapSettings) -> str:
    if cap <= 0:
        return BUDGET_UNKNOWN
    if used * 100 >= cap * _dec(settings.stop_pct):
        return BUDGET_STOP
    return BUDGET_ALERT if used * 100 >= cap * _dec(settings.alert_pct) else BUDGET_OK


def _dec(value) -> Decimal:
    return Decimal(str(value))
