"""Story F8 criteria 1 and 3: the allocation sums exactly to the recorded plan cost; no recorded cost means unknown."""

import pytest

from fno.budget.allocation import UNMEASURED, allocate


def usage(purpose, who, minutes):
    book = who if who.startswith("book") else ""
    return {"purpose": purpose, "book": book, "role_or_bundle": "" if book else who, "minutes": str(minutes)}


THREE_WAYS = [usage("books_and_roles", "book2_hybrid", 10), usage("books_and_roles", "book3_ai", 10),
              usage("development", "builder", 10)]  # fmt: skip


@pytest.mark.parametrize("cost", [1000.0, 1000.01, 1699.0, 0.02, 2083.33])
def test_parts_sum_exactly_to_the_plan_cost_even_when_rounding_is_uneven(cost):
    parts = allocate("2026-10", cost, THREE_WAYS).allocated_rs
    assert round(sum(parts.values()) * 100) == round(cost * 100)
    assert max(parts.values()) - min(parts.values()) <= 0.01  # equal minutes: at most one paisa apart


def test_a_hand_computed_month():
    rows = [usage("books_and_roles", "book2_hybrid", 30), usage("development", "builder", 90)]
    parts = allocate("2026-10", 2000.0, rows).allocated_rs
    assert parts == {("books_and_roles", "book2_hybrid", ""): 500.0, ("development", "", "builder"): 1500.0}


def test_minutes_of_the_same_share_add_up():
    rows = [usage("development", "builder", 1.5), usage("development", "builder", 2.5)]
    assert allocate("2026-10", 100.0, rows).minutes == {("development", "", "builder"): 4.0}


def test_no_recorded_plan_cost_is_flagged_and_unknown_never_zero():
    allocation = allocate("2026-10", None, THREE_WAYS)
    assert set(allocation.allocated_rs.values()) == {None}
    assert "no Claude plan cost recorded" in allocation.flagged


def test_a_cost_with_no_measured_usage_stays_whole_as_unmeasured():
    allocation = allocate("2026-10", 1700.0, [])
    assert allocation.allocated_rs == {UNMEASURED: 1700.0} and not allocation.flagged


def test_a_negative_plan_cost_is_refused():
    with pytest.raises(ValueError, match="negative"):
        allocate("2026-10", -10.01, THREE_WAYS)
