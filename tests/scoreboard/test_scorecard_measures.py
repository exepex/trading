"""Story S6 criteria 2-4: net without the best trade, the profit factor, maximum drawdown and worst day, and the t-check
(a printed warning that never changes `claim_allowed`)."""

import math
import statistics
from datetime import date, timedelta

import pytest

from fno.scoreboard.sections import _judged
from fno.scoreboard.series import DailySeries
from fno.scoreboard.t_check import DISAGREES, t_bound
from fno.scoreboard.trade_measures import NO_LOSS, NO_TRADE, drawdown, trade_measures
from fno.scoreboard.uncertainty import Uncertainty

DAY0 = date(2026, 1, 1)


def series(nets, risks=None):
    days = tuple(DAY0 + timedelta(i) for i in range(len(nets)))
    return DailySeries(days, tuple(nets), tuple(risks if risks is not None else [1000.0] * len(nets)))


def test_net_without_the_best_trade_and_the_profit_factor():
    m = trade_measures([9000.0, -4000.0, 1000.0, 0.0], open_trades=1)
    assert (m["net_without_best_rs"], m["profit_factor"], m["winners"], m["losers"]) == (-3000.0, 2.5, 2, 1)
    assert (m["gains_rs"], m["losses_rs"], m["open_left_out"]) == (10000.0, -4000.0, 1)


def test_the_profit_factor_is_undefined_not_infinite_with_no_losing_trade_and_everything_is_null_with_no_trade():
    winners_only = trade_measures([500.0, 200.0], 0)
    assert (winners_only["profit_factor"], winners_only["profit_factor_reason"]) == (None, NO_LOSS)
    empty = trade_measures([], 0)
    assert (empty["net_without_best_rs"], empty["profit_factor"], empty["profit_factor_reason"]) == (
        None,
        None,
        NO_TRADE,
    )


def test_drawdown_and_worst_day_with_their_dates_and_share_of_the_brake():
    s = series([1000.0, -3000.0, 500.0, -2000.0, 4000.0])  # cumulative 1,000 -2,000 -1,500 -3,500 500
    d = drawdown(s, 120000.0)
    assert (d["max_drawdown_rs"], d["drawdown_from"], d["drawdown_to"]) == (4500.0, "2026-01-01", "2026-01-04")
    assert (d["worst_day_rs"], d["worst_day"]) == (-3000.0, "2026-01-02")
    assert d["max_drawdown_share_of_brake"] == pytest.approx(4500 / 120000) and d["worst_day_share_of_brake"] == 0.025
    assert drawdown(series([-100.0]), None)["max_drawdown_rs"] == 100.0  # the running high starts at 0


def blocks(nets, risks):
    """20 sessions per block: each block's net and risk on its first session, zero on the other 19."""
    n, r = [], []
    for net, risk in zip(nets, risks, strict=True):
        n += [net] + [0.0] * 19
        r += [risk] + [0.0] * 19
    return series(n, r)


def test_the_t_bound_known_answer_on_6_blocks_with_unequal_risk():
    nets, risks = [100, 200, 0, 300, 100, 500], [1000, 2500, 1000, 1500, 1000, 1000]
    ratio = 1200 / 8000  # 0.15
    z = [(n - ratio * r) / (8000 / 6) for n, r in zip(nets, risks, strict=True)]
    expected = ratio - 2.015 * statistics.stdev(z) / math.sqrt(6)  # t(0.95, 5) = 2.015
    assert t_bound(blocks(nets, risks)) == (pytest.approx(expected), 6, 0)


def test_the_t_bound_needs_two_whole_blocks_and_leaves_the_oldest_remainder_out():
    assert t_bound(series([10.0] * 39))[:2] == (None, 1)
    bound, k, left_out = t_bound(series([10.0] * 40))
    assert bound is not None and k == 2 and left_out == 0
    assert t_bound(series([10.0] * 45))[1:] == (2, 5)


def test_a_disagreement_is_printed_and_never_changes_the_claim():
    noisy = blocks([1000, -900, 1200, -1100], [1000] * 4)  # t bound well below zero
    claim = Uncertainty(0.01, True, True, "lower bound and whole-period net above zero")
    judged = _judged(claim, noisy)
    assert judged["claim_allowed"] is True and judged["t_check"]["agrees_with_bootstrap"] is False
    assert judged["reason"].endswith(DISAGREES)


def test_without_a_brake_every_share_is_null_and_scoreboard_as_label_says_no_marks():
    from fno.scoreboard.trade_measures import BY_DECISION_DAY

    d = drawdown(series([100.0, 200.0]), None, BY_DECISION_DAY)
    assert (d["worst_day_share_of_brake"], d["max_drawdown_share_of_brake"], d["label"]) == (
        None,
        None,
        BY_DECISION_DAY,
    )
    assert drawdown(series([100.0, 200.0]), 120000.0)["worst_day_share_of_brake"] == 0.0
