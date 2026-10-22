"""Protocol sections 10-12: the one-sided p (block of 2, floor 30), Holm across one family, the four-part nomination
rule, drawdown and the worst month."""

from datetime import date, timedelta

import edge1study.stats as stats
import numpy as np
import pytest
from edge1study.stats import drawdown, holm_family, nominated, one_sided_p, worst_month
from edge1study.trade import TAKEN, Trade

from .edge1_fakes import cycle


def trade(net: float, day: date) -> Trade:
    return Trade(TAKEN, cycle(), "T21", exit_day=day, net=net)


def test_a_clear_positive_mean_has_a_small_p_and_a_zero_mean_does_not():
    rng = np.random.default_rng(1)
    assert one_sided_p(list(rng.normal(500, 300, 45)), 0) < 0.001
    centred = rng.normal(0, 300, 45)
    assert one_sided_p(list(centred - centred.mean()), 0) > 0.4


def test_below_30_trades_there_is_no_test():
    assert one_sided_p([100.0] * 29, 0) == 1.0


def test_the_bootstrap_uses_g4s_code_with_a_block_of_2(monkeypatch):
    seen = {}

    def fake(values, k, resamples, block):
        seen.update(k=k, resamples=resamples, block=block)
        return np.zeros(resamples)

    monkeypatch.setattr(stats, "resampled_means", fake)
    one_sided_p([1.0] * 40, 7)
    assert seen == {"k": 7, "resamples": 10_000, "block": 2}


def test_holm_is_one_family_across_both_indices():
    found = holm_family({"NIFTY SC2 T21": 0.01, "BANKNIFTY SC2 T21": 0.02, "NIFTY SF EXP": 0.5})
    assert found == {"NIFTY SC2 T21": True, "BANKNIFTY SC2 T21": True, "NIFTY SF EXP": False}
    assert holm_family({"a": 0.02, "b": 0.03, "c": 0.04})["a"] is False  # 0.02 >= 0.05 / 3


def row(**changes):
    base = {"holm": True, "p": 0.01, "mean_net_pad2": 10.0, "all_mean_net": 5.0, "all_mean_net_pad2": 1.0,
            "run1_mean_net": 3.0}  # fmt: skip
    return {**base, **changes}


@pytest.mark.parametrize("field,value", [("holm", False), ("mean_net_pad2", -1.0), ("all_mean_net", -1.0),
                                         ("all_mean_net_pad2", -0.5), ("run1_mean_net", -2.0)])  # fmt: skip
def test_each_nomination_condition_is_needed(field, value):
    assert nominated({"x": row(**{field: value})}) == []


def test_at_most_two_are_nominated_by_p():
    rows = {"a": row(p=0.03), "b": row(p=0.01), "c": row(p=0.02)}
    assert nominated(rows) == ["b", "c"]


def test_drawdown_and_worst_month():
    start = date(2025, 1, 30)
    trades = [trade(net, start + timedelta(days=31 * i)) for i, net in enumerate([100, -300, 50, -100, 400])]
    assert drawdown(trades) == pytest.approx(-350.0)  # from +100 down to -250
    assert worst_month(trades) == ("2025-03", -300.0)
