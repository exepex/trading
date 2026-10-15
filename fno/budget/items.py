"""Design v2 section 8.1's cost items for one month, from the owner's `accounting/operating_costs.csv` (story C1's
file): the cash spent on each item (None when nothing is recorded: "not recorded", never zero), and the new-cost rule:
any recorded cost other than the two running before 15 Oct 2026, or of an item not in 8.1, needs the owner's written
yes, shown by a `DESK_DECISIONS` row cited in the row's `source`."""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import (
    BUDGET_ITEMS,
    EXISTING_COST_ITEMS,
    ITEM_AZURE_POSTGRES,
    ITEM_CLAUDE_PLAN,
    ITEM_GITHUB_DRIVE,
    ITEM_GROWW_API,
    ITEM_PAID_DATA,
    ITEM_RECORDER_HOSTING,
)

DECISION_CITATION = "DESK_DECISIONS"
NEEDS_YES = "{month} {item} Rs {amount:,.2f}: a new recurring cost needs the owner's written yes (cite its {cite} row)"
CAPS = {  # what 8.1 sets for each item (the AI cap itself is computed in cap.py)
    ITEM_CLAUDE_PLAN: "AI minutes cap for books and roles (below)",
    ITEM_GITHUB_DRIVE: "no cap needed (free: public repositories; Drive within the owner's storage)",
    ITEM_AZURE_POSTGRES: "no cap set; owner records the cost",
    ITEM_GROWW_API: "no cap set; owner records any charge",
    ITEM_RECORDER_HOSTING: "a Claude routine (owner, 15 Oct 2026): measured as data_routines minutes, not a cash cost",
    ITEM_PAID_DATA: "none without an idea past the cost wall; owner approves each",
}


@dataclass(frozen=True)
class ItemLine:
    item: str
    cash_rs: float | None  # None: not recorded for the month
    cap: str


def month_items(costs: list[dict], month: str) -> list[ItemLine]:
    rows = [row for row in costs if row["month"] == month]
    return [ItemLine(item, _cash(rows, item), CAPS[item]) for item in BUDGET_ITEMS]


def plan_cost(costs: list[dict], month: str) -> float | None:
    return _cash([row for row in costs if row["month"] == month], ITEM_CLAUDE_PLAN)


def unapproved_costs(costs: list[dict], month: str) -> list[str]:
    """One line per recorded cost of the month that needs the owner's written yes and cites none."""
    return [
        NEEDS_YES.format(month=month, item=row["item"], amount=float(row["amount_rs"]), cite=DECISION_CITATION)
        for row in costs
        if row["month"] == month
        and float(row["amount_rs"]) > 0
        and row["item"] not in EXISTING_COST_ITEMS
        and DECISION_CITATION not in row["source"]
    ]


def unknown_items(costs: list[dict], month: str) -> list[str]:
    return sorted({row["item"] for row in costs if row["month"] == month and row["item"] not in BUDGET_ITEMS})


def _cash(rows: list[dict], item: str) -> float | None:
    amounts = [float(row["amount_rs"]) for row in rows if row["item"] == item]
    return sum(amounts) if amounts else None
