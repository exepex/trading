"""Protocol section 7 and 9 metrics (story B3) on hand-made opportunities."""

from dataclasses import replace
from datetime import date

import pytest
from policy_fixtures import opportunity

from fno.constants import CycleStatus
from fno.research_engine.metrics import financial_year, longest_losing_run, max_drawdown, policy_summary


def test_runs_and_drawdown():
    assert longest_losing_run([-1, -2, 0, -3, -4, -5, 6]) == 3
    assert max_drawdown([100, -50, -100, 30, 200]) == 150  # peak 100 -> trough -50
    assert max_drawdown([-10, -20]) == 30  # the start counts as a peak


def test_financial_year_runs_april_to_march():
    assert financial_year(date(2024, 3, 31)) == "2023-24" and financial_year(date(2024, 4, 1)) == "2024-25"


def test_policy_summary_counts_every_opportunity_and_keeps_traded_only_apart():
    opportunities = [
        opportunity(0, {}, {"SC": 1000.0}),
        opportunity(1, {}, {"SC": -400.0}),
        opportunity(2, {}, {"SC": 5000.0}, {"SC": CycleStatus.UNFILLABLE}),  # not traded: scores 0
        opportunity(3, {}, {"SC": 700.0}),
    ]
    chosen = ["SC", "SC", "SC", None]
    s = policy_summary(opportunities, chosen, tax_rate=0.312)
    assert (s["opportunities"], s["total_net"], s["mean_net"]) == (4, 600.0, 150.0)
    assert (s["traded"], s["traded_total_net"], s["win_rate_traded"]) == (2, 600.0, 0.5)
    assert s["status_counts"] == {"no_trade": 1, "traded": 2, "unfillable": 1}
    assert s["worst_opportunity"] == -400.0 and s["largest_modelled_max_loss"] == 9000.0
    assert s["net_by_year"] == {"2019": 600.0}
    assert s["tax_by_financial_year"]["2018-19"] == {"net": 600.0, "tax": pytest.approx(187.2)}


def test_traded_exits_beyond_the_payoff_bounds_are_counted_with_their_net():
    """B2's report-only flag: a flagged exit still counts in every total; its count and net are shown beside them."""
    opportunities = [opportunity(i, {}, {"SC": net}) for i, net in enumerate((1000.0, -400.0, 300.0))]
    flagged = replace(opportunities[1].results["SC"], exit_outside_payoff=True)
    opportunities[1] = replace(opportunities[1], results={**opportunities[1].results, "SC": flagged})
    s = policy_summary(opportunities, ["SC", "SC", None], tax_rate=0.312)
    assert (s["exits_outside_payoff"], s["exits_outside_payoff_net"], s["total_net"]) == (1, -400.0, 600.0)
    assert policy_summary(opportunities, [None, None, None], tax_rate=0.312)["exits_outside_payoff"] == 0


def test_a_losing_financial_year_pays_no_tax_and_does_not_carry_forward():
    opportunities = [opportunity(0, {}, {"SC": -900.0}), opportunity(15, {}, {"SC": 500.0})]  # Jan 2019, mid 2020
    s = policy_summary(opportunities, ["SC", "SC"], tax_rate=0.312)
    assert s["tax_by_financial_year"] == {
        "2018-19": {"net": -900.0, "tax": 0.0},
        "2020-21": {"net": 500.0, "tax": 156.0},
    }
