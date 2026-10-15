"""The month's Claude plan cost split by measured minutes (story F8, formula `minutes_share_v1`, to be frozen by S1).
Each (purpose, book, role) gets cost x its minutes / all minutes, in paise, with the paise left by rounding given to
the largest remainders, so the parts sum exactly to the recorded cost. The result is "allocated, not a bill": the cash
spent is the plan's fee, shown apart. No recorded cost: every part is unknown (None), never zero."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

FORMULA = "minutes_share_v1"
ALLOCATED_LABEL = "allocated, not a bill"
UNMEASURED = ("unmeasured", "", "no measured usage")  # where the cost goes in a month with no measured minutes

Share = tuple[str, str, str]  # (purpose, book, role_or_bundle)


@dataclass(frozen=True)
class Allocation:
    month: str
    plan_cost_rs: float | None  # None: the owner has not recorded the month's fee
    minutes: dict[Share, float]
    allocated_rs: dict[Share, float | None]

    @property
    def flagged(self) -> str:
        return (
            "" if self.plan_cost_rs is not None else f"{self.month}: no Claude plan cost recorded; allocation unknown"
        )


def minutes_by_share(usage_rows: list[dict]) -> dict[Share, float]:
    minutes: dict[Share, float] = defaultdict(float)
    for row in usage_rows:
        minutes[(row["purpose"], row["book"], row["role_or_bundle"])] += float(row["minutes"])
    return dict(sorted(minutes.items()))


def allocate(month: str, plan_cost_rs: float | None, usage_rows: list[dict]) -> Allocation:
    minutes = minutes_by_share(usage_rows)
    if plan_cost_rs is None:
        return Allocation(month, None, minutes, dict.fromkeys(minutes))
    total = sum(minutes.values())
    if total <= 0:
        return Allocation(month, plan_cost_rs, minutes, {UNMEASURED: plan_cost_rs})
    return Allocation(month, plan_cost_rs, minutes, _split(round(plan_cost_rs * 100), minutes, total))


def _split(paise: int, minutes: dict[Share, float], total: float) -> dict[Share, float]:
    exact = {share: paise * value / total for share, value in minutes.items()}
    parts = {share: int(value) for share, value in exact.items()}
    left = paise - sum(parts.values())
    for share in sorted(exact, key=lambda s: (parts[s] - exact[s], s))[:left]:  # largest remainders first
        parts[share] += 1
    return {share: part / 100 for share, part in parts.items()}
