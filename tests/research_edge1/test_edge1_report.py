"""Protocol section 12's figures on hand-made trades: incomplete exits counted and kept out of the decided mean but in
the all-trades mean, reasons for untaken cycles, and return on margin with its "unchecked" label."""

from datetime import date

import pytest
from edge1study.margin import EntryMargin
from edge1study.report import MARGIN_LABEL, figures
from edge1study.trade import CAP, T21, TAKEN, Trade

from fno.research_engine.cycles import Cycle


def trade(net, month=1, incomplete=False, status=TAKEN):
    cycle = Cycle(date(2021, month, 28), date(2020, 12, 1), date(2020, 12, 2), date(2021, month, 7))
    return Trade(status, cycle, T21, 200.0, 25, (), 60.0, date(2021, month, 7), "planned", incomplete, False,
                 net + 50.0, 30.0, 20.0, net)  # fmt: skip


def test_incomplete_exits_are_counted_kept_out_of_the_decided_mean_and_in_the_all_trades_mean():
    trades = [trade(100.0), trade(-50.0, 2), trade(-1000.0, 3, incomplete=True), trade(0.0, status=CAP)]
    found = figures(trades)
    assert (found["cycles"], found["taken"], found["complete"], found["incomplete_exits"]) == (4, 3, 2, 1)
    assert found["mean_net"] == pytest.approx(25.0) and found["all_mean_net"] == pytest.approx(-950.0 / 3)
    assert found["not_taken"] == {CAP: 1} and found["proxy_share"] == pytest.approx(0.3333)
    assert found["worst_trade"] == -50.0 and found["worst_month"] == ["2021-02", -50.0]
    assert "margin" not in found


def test_return_on_margin_is_net_over_initial_margin_and_labelled_unchecked():
    trades = [trade(100.0), trade(-50.0, 2), trade(0.0, status=CAP)]
    found = figures(trades, [EntryMargin(1000.0), EntryMargin(None, "no SPAN file")])["margin"]
    assert found["label"] == MARGIN_LABEL == "calculator only, unchecked"
    assert found["trades_with_margin"] == 1 and found["mean_return_on_margin"] == pytest.approx(0.1)
    assert found["no_margin"] == {"no SPAN file": 1}
