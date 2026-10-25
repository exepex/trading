"""Story F5 criteria 5 and 9: Book 2's orders are Book 1's `ReplayedOrders` over the committed run, its evaluator
rebuilt from the stored picks and its C4 validator from each pick's stored rule default and the recorded counts, so
D3's replay reproduces every record; a `choose_width` run orders the rebuilt width; a C4-blocked or shadow-only choice
is never ordered (the default is, for shadow-only); any edit of the stored inputs refuses every order; each trade
exits on the time exit fixed at its decision (Book 1's `PlaybookExitRules` over Book 2's records)."""

import json
from datetime import datetime, time

import pytest

from fno.book2.orders import Book2Orders
from fno.books import book1_exits
from fno.books.book1_exits import PlaybookExitRules
from fno.books.book1_records import decided_exit_days
from fno.constants import BOOK2_HYBRID
from fno.desk.daily_ports import OrdersRefused
from fno.desk.pack_items import canonical_json
from fno.desk.status import OpenPosition
from fno.models import IST
from fno.playbook.decision_inputs import DayInputs
from fno.playbook.decision_run import replay
from fno.playbook.opportunities import OpportunityFinder
from fno.research_engine.cycles import TradingDays
from fno.research_engine.ledger import Git
from tests.book1.openings import open_trades
from tests.book2.validator_replay import replay_validator
from tests.book3.builders import commit, init_repo
from tests.book3.engine_builders import validator
from tests.checks.builders import CALENDAR
from tests.decisions.builders import SAME_CODE
from tests.playbook.evaluation_builders import DAY

from .decider_builders import ALL_ALLOWED, P, R, accepted, decider, decision, evaluators, repository, slot

DECIDED_AT = datetime.combine(DAY, time(15, 11), IST)
FINDER = OpportunityFinder(TradingDays(CALENDAR))


def decided(root, slots, actions=None):
    repository(root, actions=actions)
    return decider(root).decide(accepted(decision(slots))).run


def orders(root, run):
    book2_orders = Book2Orders(evaluators(), SAME_CODE, lambda: validator(root, book=BOOK2_HYBRID))
    return {o.decision_id: o for o in book2_orders.orders(BOOK2_HYBRID, run, DECIDED_AT)}


def terms(order):
    return order.proposal.terms.width, order.proposal.terms.lots


def test_a_follow_rule_run_orders_both_defaults_at_their_built_terms(tmp_path):
    placed = orders(tmp_path, decided(tmp_path, [slot(P), slot(R)]))
    assert {k: terms(o) for k, o in placed.items()} == {P: (50, 2), R: (100, 1)} and all(
        o.risk.ok for o in placed.values()
    )


def test_a_choose_width_run_orders_the_rebuilt_width_not_the_default_s(tmp_path):
    placed = orders(tmp_path, decided(tmp_path, [slot(P, "trade", P, lots=1), slot(R, "trade", R, width=50)]))
    assert {k: terms(o) for k, o in placed.items()} == {P: (50, 1), R: (50, 1)}


def test_a_no_trade_run_orders_nothing(tmp_path):
    assert orders(tmp_path, decided(tmp_path, [slot(P, "no_trade"), slot(R, "no_trade")])) == {}


def test_a_c4_blocked_choice_is_never_ordered(tmp_path):
    run = decided(tmp_path, [slot(P), slot(R, "trade", R, width=50)], {**ALL_ALLOWED, "choose_width": "forbidden"})
    assert set(orders(tmp_path, run)) == {P}


def test_a_shadow_only_choice_orders_the_default(tmp_path):
    run = decided(tmp_path, [slot(P), slot(R, "trade", R, width=50)], {**ALL_ALLOWED, "choose_width": "shadow-only"})
    assert terms(orders(tmp_path, run)[R]) == (100, 1)


def test_d3_s_replay_reproduces_every_record_with_book2_s_validator(tmp_path):
    run = decided(tmp_path, [slot(P, "trade", P, lots=1), slot(R, "trade", R, width=50)])
    inputs = DayInputs.from_json(json.loads((run / "inputs.json").read_text()))
    assert inputs.rule_defaults == {P: "trade", R: "trade", "no_trade": "trade"}
    stored = evaluators().from_stored(inputs.selection, inputs.replay_arguments()[2])
    assert replay(run, stored, SAME_CODE, validator=replay_validator(tmp_path, inputs)) == []


@pytest.mark.parametrize("edit", ["width", "default", "rule_defaults"])
def test_an_edited_stored_input_refuses_every_order(tmp_path, edit):
    run = decided(tmp_path, [slot(P), slot(R, "trade", R, width=50)])
    inputs = json.loads((run / "inputs.json").read_text())
    if edit == "width":
        inputs["selection"][-1]["width"] = 100.0
    elif edit == "default":
        inputs["selection"][-1]["default"]["width"] = 50.0
    else:
        inputs["book2_rule_defaults"][R] = "no trade"
    (run / "inputs.json").write_bytes(canonical_json(inputs))
    with pytest.raises(OrdersRefused):
        orders(tmp_path, run)


def test_the_records_name_the_rule_it_departed_from(tmp_path):
    """A vetoed default reads rule default "trade", chosen "no trade": the paired comparison scoreboard A needs."""
    run = decided(tmp_path, [slot(P), slot(R, "no_trade")])
    records = {r["opportunity_id"]: r for r in (json.loads(p.read_text()) for p in run.glob("*.json"))
               if "opportunity_id" in r}  # fmt: skip
    assert (records[R]["rule_default"], records[R]["chosen_action"]) == ("trade", "no trade")
    assert (records[P]["rule_default"], records[P]["chosen_action"]) == ("trade", "trade")


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "sent"


def test_the_exit_is_fixed_at_the_decision_and_an_edited_version_file_never_moves_it(tmp_path, monkeypatch):
    init_repo(tmp_path)
    run = decided(tmp_path, [slot(P), slot(R, "no_trade")])
    commit(tmp_path, "the decision")
    [trade_id] = open_trades(tmp_path, BOOK2_HYBRID, DAY, run.name, Git(tmp_path).head())
    [(decided_day, version)] = decided_exit_days(tmp_path, BOOK2_HYBRID, FINDER).exits.values()
    position = OpenPosition(trade_id, version, "d", (), 0.0, DECIDED_AT, "exec", "", ())
    monkeypatch.setattr(book1_exits, "open_positions", lambda records: [position])
    edited = "name: sc-p\nexit_days_before_expiry: 5\n"  # today's file says otherwise: never read for the day
    alerts = Alerts()
    rules = PlaybookExitRules(lambda book: decided_exit_days(tmp_path, book, FINDER), lambda v: edited,
                              lambda b: None, alerts).rules(BOOK2_HYBRID)  # fmt: skip
    [rule] = rules[trade_id]
    assert rule.exit_day == decided_day and version == "sc-p-v1"
