"""The decided figures judge 473's surviving plants touched: the tail threshold (2 x credit), G1's bound on the gross
spread, settlement STT on in-the-money long legs only, run 2's run-1 mean from the decided (complete-trade) mean, and
run 1's four years."""

from datetime import date

import edge1study.runs as runs
import pytest
from edge1study.runs import g1, run2
from edge1study.stats import g1_inputs
from edge1study.structures import SC2, structure
from edge1study.trade import EXP, TAKEN, Trade, run_trade

from fno.factory.constants import BOUND_LEVEL
from fno.factory.t_bound import lower_bound
from fno.research_engine.cycle_costs import PositionCosts

from .edge1_fakes import CHARGES, DAYS, cycle, flat_prices, panel, terms
from .test_edge1_runs import Calendar, market, no_margin


def trade(gross, charges, credit=60.0, lot=25):
    return Trade(TAKEN, cycle(), "T21", credit=credit, lot=lot, gross=gross, charges=charges, pads=0.0,
                 net=gross - charges)  # fmt: skip


def test_a_tail_trade_loses_more_than_twice_its_credit():
    # credit 60 x 25 units = 1,500: a 3,100 loss is a tail at 2x (> 3,000), not at 3x (> 4,500)
    found = g1_inputs([trade(-3_100.0, 0.0), trade(100.0, 0.0), trade(100.0, 0.0), trade(100.0, 0.0)], 4.0)
    assert found.tail_share == pytest.approx(0.25) and found.tail_mean_loss == pytest.approx(3_100.0)


def test_g1s_bound_uses_the_gross_spread_and_run_1s_four_years():
    trades = [trade(1_000.0 + 50 * (i % 4), 10.0 + 200 * (i % 2)) for i in range(24)]  # net spread differs from gross
    found = g1(trades)
    inputs = g1_inputs(trades, 4.0)
    assert found["bound"] == pytest.approx(lower_bound(inputs.mean_gross, inputs.sd_gross, 24, BOUND_LEVEL))
    assert inputs.sd_gross != pytest.approx(inputs.sd_net)
    assert found["inputs"]["per_year"] == pytest.approx(6.0)  # 24 trades over 4 years


def test_settlement_charges_stt_on_in_the_money_long_legs_only():
    breach = run_trade(structure(SC2), panel({}), cycle(), terms(65, 1.0), EXP, DAYS, lambda e: 24_500.0)
    entry = [flat_prices(23_000.0)[leg.contract] for leg in breach.legs]
    opening = PositionCosts(terms(65, 1.0)).charges(list(breach.legs), entry, True)
    itm = [leg for leg in breach.legs if leg.intrinsic(24_500.0) > 0]
    stt = sum(leg.intrinsic(24_500.0) * 65 * CHARGES["stt_exercise_pct"] / 100 for leg in itm if leg.bought)
    expected = len(itm) * 20.0 * 1.18 + stt
    assert any(not leg.bought for leg in itm) and any(leg.bought for leg in itm)
    assert breach.charges - opening == pytest.approx(expected)


def test_run_2_compares_with_run_1s_decided_mean_not_the_all_trades_mean(monkeypatch):
    selection = runs.run1({"NIFTY": market()}, Calendar(), CHARGES, no_margin, {"NIFTY": 8})
    chosen = selection["NIFTY SC2 T21"]
    chosen["g1"]["passed"] = True
    chosen["pad1"] = {**chosen["pad1"], "mean_net": 5.0, "all_mean_net": -5.0}
    monkeypatch.setattr(runs, "one_sided_p", lambda nets, k: 0.001)
    found = run2({"NIFTY": market()}, Calendar(), CHARGES, no_margin, selection, {"NIFTY": date(2023, 8, 31)})
    assert found["variants"]["NIFTY SC2 T21"]["run1_mean_net"] == 5.0
