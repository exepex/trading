"""Three ledgers (story C1): trade net, account result after running costs, assumed tax; they always reconcile."""

from datetime import date

import pytest

from fno.accounting.ledgers import (
    DEFAULT_TAX_RATE_PCT,
    Ledgers,
    Order,
    Trade,
    TradeLine,
    financial_year,
    read_cost_categories,
    read_operating_costs,
    trade_line,
)
from fno.config import ROOT, load_config
from fno.costs import order_charges

CHARGES = load_config(ROOT / "config.yaml")["charges"]


def line(net: float, day: date) -> TradeLine:
    return TradeLine("t", day, gross=net, pads=0.0, charges={})


def test_the_known_answer_year_from_the_story():
    trades = [line(10_000, date(2026, 5, 10)), line(-4_000, date(2026, 6, 10)), line(6_000, date(2026, 7, 10))]
    costs = read_operating_costs("month,item,category,amount_rs,source\n2026-06,API,ai,3000,invoice 1\n")
    ledgers = Ledgers(trades, costs, read_cost_categories("category,deductible,note\nai,yes,x\n"))
    year = ledgers.tax_by_year()["2026-27"]
    assert year["trade_net"] == 12_000 and year["account_result"] == 9_000 and year["tax_base"] == 9_000
    assert year["tax"] == pytest.approx(2_808.0) and year["after_tax"] == pytest.approx(6_192.0)
    assert "assumed scenario" in year["label"] and DEFAULT_TAX_RATE_PCT == 31.2
    assert ledgers.reconciles()


def test_a_losing_year_pays_no_modelled_tax_and_says_carry_forward_is_not_modelled():
    year = Ledgers([line(-5_000, date(2026, 8, 1))], [], {}).tax_by_year()["2026-27"]
    assert year["tax"] == 0 and year["tax_base"] == -5_000 and "carry-forward" in year["note"]


def test_only_declared_categories_reduce_the_tax_base():
    costs = read_operating_costs(
        "month,item,category,amount_rs,source\n2026-06,API,ai,1000,inv\n2026-06,coffee,other,500,receipt\n"
    )
    year = Ledgers([line(10_000, date(2026, 6, 5))], costs, {"ai": True, "other": False}).tax_by_year()["2026-27"]
    assert year["account_result"] == 8_500 and year["tax_base"] == 9_000  # coffee costs money but is not deducted


def test_financial_years_run_april_to_march():
    assert financial_year(date(2025, 3, 31)) == "2024-25" and financial_year(date(2025, 4, 1)) == "2025-26"
    ledgers = Ledgers([line(1_000, date(2025, 3, 31)), line(2_000, date(2025, 4, 1))], [], {})
    assert set(ledgers.tax_by_year()) == {"2024-25", "2025-26"}


def test_trade_charges_come_from_the_one_charges_model_and_pads_are_separate():
    trade = Trade(
        "fly",
        date(2026, 11, 2),
        (Order("sell", 150.0, 65, pad=1.0), Order("buy", 40.0, 65, pad=1.0),  # entry
         Order("buy", 120.0, 65, pad=1.0), Order("sell", 30.0, 65, pad=1.0)),  # exit
    )  # fmt: skip
    result = trade_line(trade, CHARGES)
    assert result.gross == pytest.approx((150 - 40 - 120 + 30) * 65)
    assert result.pads == pytest.approx(4 * 1.0 * 65)  # Rs 1 per unit on each of four orders
    expected_charges = sum(
        order_charges(price, 65, side, CHARGES)
        for side, price in (("sell", 149), ("buy", 41), ("buy", 121), ("sell", 29))
    )
    assert sum(result.charges.values()) == pytest.approx(expected_charges)
    assert result.net == pytest.approx(result.gross - result.pads - expected_charges)


def test_bad_cost_rows_are_refused():
    with pytest.raises(ValueError):
        read_operating_costs("month,item,amount_rs\n2026-06,API,10\n")
    with pytest.raises(ValueError):
        read_operating_costs("month,item,category,amount_rs,source\n2026-13,API,ai,10,inv\n")


def test_the_repository_cost_files_load():
    costs = read_operating_costs((ROOT / "accounting/operating_costs.csv").read_text())
    categories = read_cost_categories((ROOT / "accounting/deductible_categories.csv").read_text())
    plan = {
        "month": "2026-10",
        "item": "Claude subscription",
        "category": "ai",
        "amount_rs": "20000",
        "source": "DESK_DECISIONS 15 Oct 2026: Claude plan cost: INR 20,000 a month",
    }  # owner, 15 Oct (story F8)
    assert costs == [plan] and categories == {"ai": True, "data": True, "compute": True, "other": False}
    assert Ledgers([], costs, categories).reconciles()


CATEGORIES = {"ai": True, "other": False}


def sample_ledgers() -> Ledgers:
    costs = read_operating_costs(
        "month,item,category,amount_rs,source\n2026-03,API,ai,700,inv\n2026-05,API,ai,1000,inv\n"
        "2026-05,coffee,other,300,receipt\n"
    )
    trades = [line(5_000, date(2026, 3, 20)), line(-2_000, date(2026, 4, 9)), line(8_000, date(2026, 5, 2))]
    return Ledgers(trades, costs, CATEGORIES)


@pytest.mark.parametrize(
    "table, period, key",
    [
        ("months", "2026-05", "trade_net"),  # a month that disagrees with the trade lines
        ("months", "2026-03", "operating_costs"),  # a month that disagrees with the raw costs
        ("years", "2026-27", "account_result"),  # a year that is not the sum of its months
        ("years", "2025-26", "tax_base"),  # a tax base that ignores the deductible costs
        ("years", "2026-27", "operating_costs"),
        ("years", "2026-27", "tax"),  # judge 10: a tax figure that is not the rate times the base
        ("years", "2026-27", "after_tax"),
    ],
)
def test_a_broken_ledger_does_not_reconcile(table, period, key):
    """Judge 6, finding 1: tamper with one figure of one table; the reconciliation must catch it."""
    ledgers = sample_ledgers()
    months, years = ledgers.by_month(), ledgers.tax_by_year()
    assert ledgers.reconciles(months, years)
    {"months": months, "years": years}[table][period][key] += 100.0
    assert not ledgers.reconciles(months, years)


def test_a_missing_or_extra_year_does_not_reconcile():
    ledgers = sample_ledgers()
    years = ledgers.tax_by_year()
    del years["2025-26"]
    assert not ledgers.reconciles(years=years)


def test_each_year_is_the_sum_of_its_months():
    ledgers = sample_ledgers()
    year = ledgers.tax_by_year()["2026-27"]
    months = ledgers.by_month()
    assert year["trade_net"] == months["2026-04"]["trade_net"] + months["2026-05"]["trade_net"] == 6_000
    assert year["tax_base"] == 6_000 - 1_000  # the coffee is not deductible


def test_an_undeclared_or_mistyped_cost_category_is_refused():
    costs = read_operating_costs("month,item,category,amount_rs,source\n2026-06,API,AI,10,inv\n")
    with pytest.raises(ValueError, match="undeclared"):
        Ledgers([], costs, CATEGORIES)


def test_category_file_needs_its_columns_and_a_yes_or_no():
    with pytest.raises(ValueError, match="columns"):
        read_cost_categories("category,deductible\nai,yes\n")
    with pytest.raises(ValueError, match="yes or no"):
        read_cost_categories("category,deductible,note\nai,maybe,x\n")


def test_a_cost_file_with_wrong_columns_is_refused_even_without_rows():
    with pytest.raises(ValueError, match="columns"):
        read_operating_costs("month,item,amount_rs\n")
