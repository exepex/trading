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
    read_deductible,
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
    ledgers = Ledgers(trades, costs, read_deductible("category,deductible,note\nai,yes,x\n"))
    year = ledgers.tax_by_year()["2026-27"]
    assert year["trade_net"] == 12_000 and year["account_result"] == 9_000 and year["tax_base"] == 9_000
    assert year["tax"] == pytest.approx(2_808.0) and year["after_tax"] == pytest.approx(6_192.0)
    assert "assumed scenario" in year["label"] and DEFAULT_TAX_RATE_PCT == 31.2
    assert ledgers.reconciles()


def test_a_losing_year_pays_no_modelled_tax_and_says_carry_forward_is_not_modelled():
    year = Ledgers([line(-5_000, date(2026, 8, 1))], [], set()).tax_by_year()["2026-27"]
    assert year["tax"] == 0 and year["tax_base"] == -5_000 and "carry-forward" in year["note"]


def test_only_declared_categories_reduce_the_tax_base():
    costs = read_operating_costs(
        "month,item,category,amount_rs,source\n2026-06,API,ai,1000,inv\n2026-06,coffee,other,500,receipt\n"
    )
    year = Ledgers([line(10_000, date(2026, 6, 5))], costs, {"ai"}).tax_by_year()["2026-27"]
    assert year["account_result"] == 8_500 and year["tax_base"] == 9_000  # coffee costs money but is not deducted


def test_financial_years_run_april_to_march():
    assert financial_year(date(2025, 3, 31)) == "2024-25" and financial_year(date(2025, 4, 1)) == "2025-26"
    ledgers = Ledgers([line(1_000, date(2025, 3, 31)), line(2_000, date(2025, 4, 1))], [], set())
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
    deductible = read_deductible((ROOT / "accounting/deductible_categories.csv").read_text())
    assert costs == [] and deductible == {"ai", "data", "compute"}
