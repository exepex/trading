"""Story BG1 criteria 1, 2, 3 and 5: every 8.1 item with cash spend or "not recorded"; the cap's levels, basis and
coverage rules; the new-cost rule with a cited, existing owner decision."""

import pytest

from fno.budget.cap import BASIS_MEASURED, CapSettings, Coverage, cap_reading, shown_pct
from fno.budget.constants import BUDGET_ITEMS
from fno.budget.items import month_items, plan_cost, unapproved_costs, unknown_items
from fno.config import load_app_config

DECISIONS = '| 20 Oct 2026 | **Groww API data plan approved** (owner: "yes") | ... |\n'
COMPLETE = Coverage()  # nothing known to be missing
SETTINGS = CapSettings(50, 80, 100, None)


def cost(item, amount, source="owner", month="2026-10"):
    return {"month": month, "item": item, "category": "ai", "amount_rs": str(amount), "source": source}


def minutes(purpose, value):
    return {"purpose": purpose, "minutes": str(value)}


def reading(rows, settings=SETTINGS, coverage=COMPLETE, month="2026-10"):
    return cap_reading(rows, settings, month, coverage)


def test_every_item_is_shown_and_a_missing_one_is_not_recorded_never_zero():
    lines = month_items([cost("Claude subscription", 1700), cost("Claude subscription", 300),
                         cost("Groww API", 0, month="2026-09")], "2026-10")  # fmt: skip
    assert [line.item for line in lines] == list(BUDGET_ITEMS)
    assert lines[0].cash_rs == 2000.0 and all(line.cash_rs is None for line in lines[1:])
    assert plan_cost([cost("Azure Database for PostgreSQL", 900)], "2026-10") is None
    assert "storage not reported yet" in lines[1].cap  # 8.1's storage line: a stated gap, not silent


@pytest.mark.parametrize("used, level", [(39.95, "ok"), (40, "alert"), (49.99, "alert"), (50, "stop"), (70, "stop")])
def test_levels_at_the_boundaries(used, level):
    result = reading([minutes("books_and_roles", used), minutes("development", 100 - used)])
    assert result.level == level and result.cap_minutes == 50


@pytest.mark.parametrize(
    "books, development, plan, level",
    [("0.68", "1.02", None, "alert"), ("0.17", "0.17", None, "stop"), ("1.16", "0", "2.9", "alert")],
)
def test_exact_boundaries_are_not_lost_to_float_rounding(books, development, plan, level):
    """Reviewer finding: 0.68 of 1.70 minutes is exactly 80% of a 0.85 cap, never 79.999...%."""
    rows = [minutes("books_and_roles", books), minutes("development", development)]
    assert reading(rows, CapSettings(50, 80, 100, plan)).level == level


def test_nothing_measured_is_unknown_and_never_called_a_lower_bound():
    assert reading([]).level == "unknown" and reading([]).pct_of_cap is None
    assert reading([], coverage=Coverage(2)).note == (
        "unknown: no minutes to measure against; 2 fired AI book session(s) not captured"
    )


def test_the_measured_basis_is_all_purposes_and_the_owner_figure_replaces_it():
    rows = [minutes("books_and_roles", 30), minutes("development", 30)]
    measured = reading(rows)
    assert (measured.basis, measured.cap_minutes, measured.pct_of_cap) == (BASIS_MEASURED, 30, 100)
    owner = reading(rows, CapSettings(50, 80, 100, 600))
    assert (owner.cap_minutes, owner.pct_of_cap, owner.level) == (300, 10, "ok") and "owner's figure" in owner.basis


def test_development_not_fully_captured_makes_the_measured_level_unknown():
    """Judge 104 must-fix 3: one book row and no captured development must not read 200% stop."""
    gap = Coverage(0, "2 development session(s) not fully captured")
    result = reading([minutes("books_and_roles", 30)], coverage=gap)
    assert result.level == "unknown" and "2 development session(s) not fully captured" in result.note
    assert result.pct_of_cap == 200.0  # the figure is shown, the level is not trusted
    assert reading([minutes("books_and_roles", 30)], CapSettings(50, 80, 100, 600), coverage=gap).level == "ok"


def test_missing_book_captures_make_ok_unknown_and_alert_a_lower_bound():
    ok = reading([minutes("books_and_roles", 10), minutes("development", 90)], coverage=Coverage(2))
    assert ok.level == "unknown" and "2 fired AI book session(s) not captured" in ok.note
    alert = reading([minutes("books_and_roles", 42), minutes("development", 58)], coverage=Coverage(1))
    assert alert.level == "alert" and alert.note.startswith("at least this level")
    owner = reading([], CapSettings(50, 80, 100, 600), coverage=Coverage(5))
    assert owner.level == "unknown" and owner.pct_of_cap == 0.0


def test_the_measured_basis_expires_after_its_last_month():
    """Owner "7 A": 50% of measured minutes for two months, then a fixed figure the owner gives (never invented)."""
    rows = [minutes("books_and_roles", 10), minutes("development", 90)]
    settings = CapSettings(50, 80, 100, None, "2026-12")
    assert reading(rows, settings, month="2026-12").level == "ok"
    expired = reading(rows, settings, month="2027-01")
    assert expired.level == "unknown" and "fixed monthly figure is owed" in expired.note
    assert reading(rows, CapSettings(50, 80, 100, 600, "2026-12"), month="2027-01").level == "ok"


def test_data_routine_minutes_count_in_the_basis_but_never_against_the_cap():
    result = reading([minutes("books_and_roles", 20), minutes("development", 20), minutes("data_routines", 60)])
    assert (result.books_and_roles_minutes, result.basis_minutes, result.level) == (20, 100, "ok")


def test_the_owner_numbers_come_from_config_and_bad_numbers_are_refused():
    settings = CapSettings.from_config(load_app_config()["budget"])
    assert (settings.share_pct, settings.alert_pct, settings.stop_pct, settings.plan_minutes) == (50, 80, 100, None)
    assert settings.basis_until == "2026-12"
    base = {"cap": "share", "books_and_roles_share_pct": 50, "alert_pct": 80, "stop_pct": 100}
    for bad in ({"alert_pct": 120}, {"books_and_roles_share_pct": 0}, {"books_and_roles_share_pct": 101}):
        with pytest.raises(ValueError, match="budget settings"):
            CapSettings.from_config(base | bad)


def test_shown_percentages_are_floored():
    assert (shown_pct(99.96), shown_pct(99.6), shown_pct(80.0)) == (99.9, 99.6, 80.0)


def test_a_new_cost_needs_an_existing_cited_owner_decision():
    cite = "DESK_DECISIONS 20 Oct 2026: Groww API data plan approved"
    wrong_date = cite.replace("20 Oct", "21 Oct")
    costs = [cost("Paid data", 500), cost("Groww API", 200, cite), cost("Groww API", 300, "not in DESK_DECISIONS"),
             cost("Groww API", 100, "DESK_DECISIONS 20 Oct 2026: made up"), cost("Groww API", 101, "not in " + cite),
             cost("Groww API", 102, wrong_date), cost("Groww API", 103, "DESK_DECISIONS 20 Oct 2026: approved"),
             cost("Claude subscription", 1700), cost("Azure Database for PostgreSQL", 900), cost("Weather feed", 50),
             cost("Recorder and monitor hosting", 0), cost("Claude subscription", -100)]  # fmt: skip
    flagged = [line.split(":")[0].removeprefix("2026-10 ") for line in unapproved_costs(costs, "2026-10", DECISIONS)]
    assert flagged == ["Paid data Rs 500.00", "Groww API Rs 300.00", "Groww API Rs 100.00", "Groww API Rs 101.00",
                       "Groww API Rs 102.00", "Groww API Rs 103.00", "Weather feed Rs 50.00",
                       "Claude subscription Rs -100.00"]  # fmt: skip
    assert unknown_items(costs, "2026-10") == ["Weather feed"]


def test_the_recorded_plan_cost_cites_the_owner_row_that_exists():
    from fno.accounting.ledgers import read_operating_costs
    from fno.config import ROOT

    costs = read_operating_costs((ROOT / "accounting/operating_costs.csv").read_text(encoding="utf-8"))
    decisions = (ROOT / "docs/DESK_DECISIONS.md").read_text(encoding="utf-8")
    assert plan_cost(costs, "2026-10") == 20000.0 and unapproved_costs(costs, "2026-10", decisions) == []
    assert costs[0]["source"] == "DESK_DECISIONS 15 Oct 2026: Claude plan cost: INR 20,000 a month"


def test_a_data_routine_gap_makes_the_measured_level_unknown_not_a_false_alert():
    """Judge 104 addendum 1: books 45 and development 55 with uncaptured data-routine minutes read 90% "alert"; the
    truth with 200 routine minutes is 30%. So the measured level is unknown until the runs are captured."""
    rows = [minutes("books_and_roles", 45), minutes("development", 55)]
    gap = Coverage(0, "", "data routines not fully captured: 0 of 9 expected run(s) recorded (3 pm quote recorder)")
    measured = reading(rows, coverage=gap)
    assert measured.level == "unknown" and "data routines not fully captured" in measured.note
    assert reading(rows + [minutes("data_routines", 200)]).level == "ok"  # the truth once captured: 30%
    assert reading(rows, CapSettings(50, 80, 100, 600), coverage=gap).level == "ok"  # the owner's figure is unaffected
