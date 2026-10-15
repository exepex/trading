"""The AI minutes cap for books and roles (story BG1; owner decision of 15 Oct 2026: half of the plan's measured session
minutes, alert at 80%, AI roles stop at 100%). The plan publishes no minutes allowance, so by default the basis is all
measured session minutes of the month (every purpose); the owner may set their own monthly figure instead."""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import BUDGET_ALERT, BUDGET_OK, BUDGET_STOP, BUDGET_UNKNOWN, PURPOSE_BOOKS_AND_ROLES

BASIS_MEASURED = "measured: all recorded session minutes of the month (books, roles and development)"
BASIS_OWNER = "owner's figure: {minutes:,.0f} plan minutes a month (config.yaml budget.plan_minutes_per_month)"
MEASURED_LIMIT = (
    "limit: the plan's real capacity is not measurable (its rate-limit data gives no minutes), so this basis moves "
    "with development: quiet development raises the books' share, busy development loosens the cap"
)


@dataclass(frozen=True)
class CapSettings:
    share_pct: float  # of the basis, for books and roles
    alert_pct: float
    stop_pct: float
    plan_minutes: float | None  # the owner's own monthly figure, if set

    @classmethod
    def from_config(cls, budget: dict) -> CapSettings:
        plan = budget.get("plan_minutes_per_month")
        return cls(float(budget["books_and_roles_share_pct"]), float(budget["alert_pct"]), float(budget["stop_pct"]),
                   float(plan) if plan is not None else None)  # fmt: skip


@dataclass(frozen=True)
class CapReading:
    books_and_roles_minutes: float
    basis_minutes: float
    cap_minutes: float
    pct_of_cap: float | None  # None: nothing to measure against
    level: str
    basis: str


def cap_reading(usage_rows: list[dict], settings: CapSettings) -> CapReading:
    used = sum(float(r["minutes"]) for r in usage_rows if r["purpose"] == PURPOSE_BOOKS_AND_ROLES)
    if settings.plan_minutes is not None:
        basis_minutes, basis = settings.plan_minutes, BASIS_OWNER.format(minutes=settings.plan_minutes)
    else:
        basis_minutes, basis = sum(float(r["minutes"]) for r in usage_rows), BASIS_MEASURED
    cap = basis_minutes * settings.share_pct / 100
    pct = 100 * used / cap if cap > 0 else None
    return CapReading(round(used, 2), round(basis_minutes, 2), round(cap, 2), pct, _level(pct, settings), basis)


def _level(pct: float | None, settings: CapSettings) -> str:
    if pct is None:
        return BUDGET_UNKNOWN
    if pct >= settings.stop_pct:
        return BUDGET_STOP
    return BUDGET_ALERT if pct >= settings.alert_pct else BUDGET_OK
