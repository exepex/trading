"""Story E6 criterion 3 and the scorecard: execution costs measured from the record equal a hand computation; C1's
ledgers carry every closed trade; open positions are shown at marks and never counted; shadow tests stay apart."""

from datetime import date

import pytest

from fno.constants import (
    BOOK1_RULES,
    OUTCOME_EXIT_ORDERED,
    OUTCOME_NOT_OPENED,
    OUTCOME_PARTIAL_FILL,
    OUTCOME_PENDING_EXIT,
    OUTCOME_REFUSED,
    SIDE_BUY,
    SIDE_SELL,
)
from fno.costs import order_charges
from fno.scorecard.report import report

from .conftest import SHADOW, START
from .history import CHARGES, EXPIRY, UNITS, event, trade

ON = date(2026, 10, 25)


def card(make_run, strategy="fly-a-v1", account=BOOK1_RULES, marks=None):
    cards, _ = make_run().run(ON, marks or {}, account, strategy, pause=False)
    [only] = cards
    return only


def test_execution_costs_measured_from_the_record_equal_a_hand_computation(root, make_run):
    trade(root, BOOK1_RULES, "fly-a-v1", "t1", START, date(2026, 10, 20), credit=50, debit=30, half=0.5)
    trade(root, BOOK1_RULES, "fly-a-v1", "t2", START, half=1.5)  # still open: two fills at 1.5 from mid
    event(root, BOOK1_RULES, "fly-a-v1", "t5", OUTCOME_PARTIAL_FILL, START, legging_cost_rs=123.45)
    event(root, BOOK1_RULES, "fly-a-v1", "t6", OUTCOME_NOT_OPENED, START, "a leg had no valid quote")
    event(root, BOOK1_RULES, "fly-a-v1", "t7", OUTCOME_REFUSED, START, "risk manager refused")
    for trade_id, ordered, closed in (("t3", 20, 23), ("t4", 21, None)):
        event(root, BOOK1_RULES, "fly-a-v1", trade_id, OUTCOME_EXIT_ORDERED, date(2026, 10, ordered))
        event(root, BOOK1_RULES, "fly-a-v1", trade_id, OUTCOME_PENDING_EXIT, date(2026, 10, ordered))
        if closed:
            event(root, BOOK1_RULES, "fly-a-v1", trade_id, "closed", date(2026, 10, closed), legging_cost_rs=10.0)
    costs = card(make_run).costs
    # 4 fills x 65 units at 0.5 and 2 fills x 65 units at 1.5: (0.5 x 4 + 1.5 x 2) / 6 = Rs 0.8333 a unit
    assert costs.units_at_quotes == 6 * UNITS and costs.half_spread_per_unit == pytest.approx(5 / 6)
    assert costs.research_pad_per_unit == 1.0
    assert costs.legging_costs_rs == pytest.approx(133.45)
    assert (costs.attempts, costs.opened, costs.not_filled, costs.refused) == (4, 2, 2, 1)  # t1 t2 opened; t5 t6 not
    assert costs.not_filled_share == 0.5
    assert costs.pending_days == (3, 4) and costs.mean_pending_days == 3.5 and costs.still_pending == ("t4",)


def test_the_ledgers_carry_every_closed_trade_at_c1_s_net(root, make_run):
    trade(root, BOOK1_RULES, "fly-a-v1", "t1", START, date(2026, 10, 20), credit=50, debit=30)
    orders = [(20.0, SIDE_BUY), (70.0, SIDE_SELL), (40.0, SIDE_BUY), (10.0, SIDE_SELL)]
    net = (50 - 30) * UNITS - sum(order_charges(price, UNITS, side, CHARGES) for price, side in orders)
    scored = card(make_run)
    assert scored.total_net == pytest.approx(net) and scored.by_month["2026-10"]["trade_net"] == pytest.approx(net)
    assert scored.tax_by_year["2026-27"]["tax"] == pytest.approx(0.312 * net)


def test_open_positions_are_shown_at_marks_and_never_counted(root, make_run):
    trade(root, BOOK1_RULES, "fly-a-v1", "t1", START, credit=50)
    marks = {(EXPIRY, 25000.0, "CE"): 400.0, (EXPIRY, 25200.0, "CE"): 300.0}
    scored = card(make_run, marks=marks)
    [mark] = scored.open_marks
    assert mark.marked_net == pytest.approx(mark.cash_flow + (300.0 - 400.0) * UNITS)
    assert scored.trade_lines == () and scored.review.positions == 0  # not a completed position
    [unmarked] = card(make_run, marks={(EXPIRY, 25000.0, "CE"): 400.0}).open_marks
    assert unmarked.marked_net is None  # a leg without a mark: never guessed


def test_shadow_tests_are_reported_apart_from_the_books(root, make_run):
    trade(root, BOOK1_RULES, "fly-a-v1", "t1", START, date(2026, 10, 20), credit=50, debit=30)
    trade(root, SHADOW, "cand-c-v1", "s1", START, date(2026, 10, 20), credit=50, debit=30)
    cards, _ = make_run().run(ON, {}, pause=False)
    text = report(cards, [])
    books, shadows = (
        text.index("== Book scorecards =="),
        [i for i, line in enumerate(text) if "Shadow tests" in line][0],
    )
    assert any("fly-a-v1 in book1_rules" in line for line in text[books:shadows])
    assert any(f"cand-c-v1 in {SHADOW} (research)" in line for line in text[shadows:])
    assert not any("cand-c" in line for line in text[books:shadows])


def test_each_version_in_one_account_is_scored_on_its_own_trades_only(root, make_run):
    trade(root, BOOK1_RULES, "fly-a-v1", "a1", START, date(2026, 10, 20), credit=50, debit=30)
    trade(root, BOOK1_RULES, "fly-b-v1", "b1", START, date(2026, 10, 20), credit=50, debit=90, half=2.0)
    trade(root, BOOK1_RULES, "fly-b-v1", "b2", START, date(2026, 10, 21), credit=50, debit=90, half=2.0)
    a, b = card(make_run, "fly-a-v1"), card(make_run, "fly-b-v1")
    assert [line.trade_id for line in a.trade_lines] == ["a1"] and [line.trade_id for line in b.trade_lines] == [
        "b1",
        "b2",
    ]
    assert a.costs.half_spread_per_unit == pytest.approx(0.5) and b.costs.half_spread_per_unit == pytest.approx(2.0)
