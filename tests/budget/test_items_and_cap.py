"""Story BG1 criteria 1, 2, 3 and 5: every 8.1 item with cash spend or "not recorded"; the cap's levels and basis; the
new-cost rule."""

import pytest

from fno.budget.cap import BASIS_MEASURED, CapSettings, cap_reading
from fno.budget.items import month_items, plan_cost, unapproved_costs, unknown_items
from fno.config import load_app_config
from fno.constants import BUDGET_ITEMS


def cost(item, amount, source="owner", month="2026-10"):
    return {"month": month, "item": item, "category": "ai", "amount_rs": str(amount), "source": source}


def minutes(purpose, value):
    return {"purpose": purpose, "minutes": str(value)}


SETTINGS = CapSettings(50, 80, 100, None)


def test_every_item_is_shown_and_a_missing_one_is_not_recorded_never_zero():
    lines = month_items([cost("Claude subscription", 1700), cost("Claude subscription", 300),
                         cost("Groww API", 0, month="2026-09")], "2026-10")  # fmt: skip
    assert [line.item for line in lines] == list(BUDGET_ITEMS)
    assert lines[0].cash_rs == 2000.0 and all(line.cash_rs is None for line in lines[1:])
    assert plan_cost([cost("Azure Database for PostgreSQL", 900)], "2026-10") is None


@pytest.mark.parametrize("used, level", [(39.95, "ok"), (40, "alert"), (49.99, "alert"), (50, "stop"), (70, "stop")])
def test_levels_at_the_boundaries(used, level):
    rows = [minutes("books_and_roles", used), minutes("development", 100 - used)]
    reading = cap_reading(rows, SETTINGS)
    assert reading.level == level and reading.cap_minutes == 50


def test_nothing_measured_is_unknown_and_never_called_a_lower_bound():
    assert cap_reading([], SETTINGS).level == "unknown" and cap_reading([], SETTINGS).pct_of_cap is None
    reading = cap_reading([], SETTINGS, missing_captures=2)
    assert reading.note == "unknown: no minutes to measure against; 2 fired AI book session(s) not captured"


def test_the_measured_basis_is_all_purposes_and_the_owner_figure_replaces_it():
    rows = [minutes("books_and_roles", 30), minutes("development", 30)]
    measured = cap_reading(rows, SETTINGS)
    assert (measured.basis, measured.cap_minutes, measured.pct_of_cap) == (BASIS_MEASURED, 30, 100)
    owner = cap_reading(rows, CapSettings(50, 80, 100, 600))
    assert (owner.cap_minutes, owner.pct_of_cap, owner.level) == (300, 10, "ok") and "owner's figure" in owner.basis


def test_the_owner_numbers_come_from_config():
    settings = CapSettings.from_config(load_app_config()["budget"])
    assert (settings.share_pct, settings.alert_pct, settings.stop_pct, settings.plan_minutes) == (50, 80, 100, None)


def test_a_new_cost_needs_a_cited_owner_decision():
    costs = [cost("Paid data", 500), cost("Groww API", 200, "DESK_DECISIONS 20 Oct 2026 row"),
             cost("Claude subscription", 1700), cost("Azure Database for PostgreSQL", 900), cost("Weather feed", 50),
             cost("Recorder and monitor hosting", 0)]  # fmt: skip
    flagged = unapproved_costs(costs, "2026-10")
    assert len(flagged) == 2 and "Paid data" in flagged[0] and "Weather feed" in flagged[1]
    assert unknown_items(costs, "2026-10") == ["Weather feed"]


@pytest.mark.parametrize(
    "books, development, plan, level",
    [("0.68", "1.02", None, "alert"), ("0.17", "0.17", None, "stop"), ("1.16", "0", "2.9", "alert")],
)
def test_exact_boundaries_are_not_lost_to_float_rounding(books, development, plan, level):
    """Reviewer finding: 0.68 of 1.70 minutes is exactly 80% of a 0.85 cap, never 79.999...%."""
    rows = [minutes("books_and_roles", books), minutes("development", development)]
    assert cap_reading(rows, CapSettings(50, 80, 100, plan)).level == level


def test_no_development_minutes_on_the_measured_basis_is_unknown_not_stop():
    reading = cap_reading([minutes("books_and_roles", 30)], SETTINGS)
    assert reading.level == "unknown" and "no minutes other than the books' and roles'" in reading.note


def test_missing_captures_make_ok_unknown_and_alert_a_lower_bound():
    ok = cap_reading([minutes("books_and_roles", 10), minutes("development", 90)], SETTINGS, missing_captures=2)
    assert ok.level == "unknown" and "2 fired AI book session(s) not captured" in ok.note
    alert = cap_reading([minutes("books_and_roles", 42), minutes("development", 58)], SETTINGS, missing_captures=1)
    assert alert.level == "alert" and alert.note.startswith("at least this level")
    owner = cap_reading([], CapSettings(50, 80, 100, 600), missing_captures=5)
    assert owner.level == "unknown" and owner.pct_of_cap == 0.0


def test_data_routine_minutes_count_in_the_basis_but_never_against_the_cap():
    rows = [minutes("books_and_roles", 20), minutes("development", 20), minutes("data_routines", 60)]
    reading = cap_reading(rows, SETTINGS)
    assert (reading.books_and_roles_minutes, reading.basis_minutes, reading.level) == (20, 100, "ok")
