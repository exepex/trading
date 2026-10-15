"""Judge 104 addendum 1 minor: the decided monthly plan cost, a recorded payment beside it, and a citation that must
exist."""

import pytest

from fno.budget.plan_cost import DecidedPlanCost, month_plan_cost

DECISIONS = "| 15 Oct 2026 | **Claude plan cost: INR 20,000 a month** (owner: ...) | ... |\n"
PLAN = {"rs_per_month": 20000, "from_month": "2026-10",
        "decision": "DESK_DECISIONS 15 Oct 2026: Claude plan cost: INR 20,000 a month"}  # fmt: skip
DECIDED = DecidedPlanCost.from_config(PLAN, DECISIONS)


def test_the_decided_figure_covers_months_from_its_first_month_only():
    assert month_plan_cost(None, DECIDED, "2027-03").allocated_from_rs == 20000.0
    before = month_plan_cost(None, DECIDED, "2026-09")
    assert (before.allocated_from_rs, before.cash_line) == (None, "not recorded")


def test_a_recorded_payment_is_the_cash_spend_and_a_difference_is_flagged():
    same = month_plan_cost(20000.0, DECIDED, "2026-10")
    assert (same.allocated_from_rs, same.cash_line, same.warning) == (20000.0, "Rs 20,000.00", "")
    other = month_plan_cost(21000.0, DECIDED, "2026-11")
    assert other.allocated_from_rs == 21000.0 and "differs from the decided Rs 20,000.00" in other.warning


def test_no_decided_figure_means_unknown_without_a_payment():
    assert month_plan_cost(None, None, "2026-11").allocated_from_rs is None
    assert DecidedPlanCost.from_config(None, DECISIONS) is None


@pytest.mark.parametrize(
    "change",
    [
        {"decision": "DESK_DECISIONS 15 Oct 2026: Claude plan cost"},
        {"decision": "made up"},
        {"rs_per_month": -1},
    ],  # fmt: skip
)
def test_a_decided_cost_must_cite_an_existing_row(change):
    with pytest.raises(ValueError, match="not a row of docs/DESK_DECISIONS.md"):
        DecidedPlanCost.from_config(PLAN | change, DECISIONS)


def test_the_config_value_cites_the_owners_real_row():
    from fno.config import ROOT, load_app_config

    decided = DecidedPlanCost.from_config(load_app_config()["budget"]["plan_cost"],
                                          (ROOT / "docs/DESK_DECISIONS.md").read_text(encoding="utf-8"))  # fmt: skip
    assert (decided.rs_per_month, decided.from_month) == (20000.0, "2026-10")
