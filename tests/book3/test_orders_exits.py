"""Story F6 criteria 14 and 15: Book 3's orders replay the committed run with its stored picks (Book 1's
`ReplayedOrders`), and each open Book 3 trade exits on the time exit fixed at its decision from the spec as the run
read it (Book 1's `PlaybookExitRules` over Book 3's store); today's spec file only feeds the alerts."""

import json
from datetime import date, datetime, time

import pytest

from fno.book3.orders import Book3Orders
from fno.book3.registry import spec_path
from fno.books import book1_exits
from fno.books.book1_exits import PlaybookExitRules
from fno.books.book1_records import decided_exit_days
from fno.constants import BOOK3_AI
from fno.desk.daily_ports import OrdersRefused
from fno.desk.pack_items import canonical_json
from fno.desk.status import OpenPosition
from fno.models import IST
from fno.playbook.documents import strategy_from_text
from fno.playbook.opportunities import OpportunityFinder
from fno.research_engine.cycles import TradingDays
from fno.research_engine.ledger import Git
from tests.book1.openings import open_trades
from tests.book3.builders import commit
from tests.book3.engine_builders import (
    DAY,
    OPPORTUNITY,
    accepted,
    decider,
    decision,
    evaluators,
    repository,
    spec,
    validator,
)  # fmt: skip
from tests.checks.builders import CALENDAR
from tests.decisions.builders import SAME_CODE

DECIDED_AT = datetime.combine(DAY, time(15, 11), IST)
FINDER = OpportunityFinder(TradingDays(CALENDAR))


def decided_run(root, trades=(OPPORTUNITY,)):
    repository(root, [spec()])
    out = decider(root).decide(accepted(root, decision(trades=list(trades))))
    commit(root, "the decision")
    return out.run


def orders(root, run):
    return Book3Orders(evaluators(), SAME_CODE, validator(root)).orders(BOOK3_AI, run, DECIDED_AT)


def test_the_committed_pick_is_ordered_once_with_c2_s_decision(tmp_path):
    [order] = orders(tmp_path, decided_run(tmp_path))
    assert (order.book, order.decision_id) == (BOOK3_AI, OPPORTUNITY) and order.risk.ok


def test_a_no_trade_run_orders_nothing(tmp_path):
    assert orders(tmp_path, decided_run(tmp_path, trades=())) == []


def test_a_c4_blocked_pick_is_never_ordered(tmp_path):
    repository(tmp_path, [spec()])
    (tmp_path / "book3/constitution-v1.yaml").write_text("version: 1\n")
    out = decider(tmp_path).decide(accepted(tmp_path, decision(trades=[OPPORTUNITY])))
    assert orders(tmp_path, out.run) == []


def test_an_unedited_canonical_rewrite_still_orders(tmp_path):
    run = decided_run(tmp_path)
    (run / "inputs.json").write_bytes(canonical_json(json.loads((run / "inputs.json").read_text())))
    assert len(orders(tmp_path, run)) == 1


@pytest.mark.parametrize("edit", ["picks", "spec"])
def test_an_edited_stored_pick_or_spec_refuses_every_order(tmp_path, edit):
    run = decided_run(tmp_path)
    inputs = json.loads((run / "inputs.json").read_text())
    if edit == "picks":
        inputs["selection"] = []
    else:
        name = next(iter(inputs["playbook"]["files"]))
        inputs["playbook"]["files"][name] += "# edited\n"
    (run / "inputs.json").write_bytes(canonical_json(inputs))
    with pytest.raises(OrdersRefused):
        orders(tmp_path, run)


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "sent"


def exits(root, alerts, monkeypatch, trade_id):
    position = OpenPosition(trade_id, "b3-sc-v1", "d", (), 0.0, DECIDED_AT, "exec", "", ())
    monkeypatch.setattr(book1_exits, "open_positions", lambda records: [position])

    def spec_text(version):
        path = root / spec_path(version)
        return path.read_text() if path.is_file() else None

    return PlaybookExitRules(lambda book: decided_exit_days(root, book, FINDER), spec_text, lambda b: None, alerts)


def test_the_exit_is_fixed_at_the_decision_and_today_s_spec_never_moves_it(tmp_path, monkeypatch):
    run = decided_run(tmp_path)
    [trade_id] = open_trades(tmp_path, BOOK3_AI, DAY, run.name, Git(tmp_path).head())
    expected = FINDER.exit_day(strategy_from_text(spec(), "spec"), date(2026, 11, 27))
    alerts = Alerts()
    [rule] = exits(tmp_path, alerts, monkeypatch, trade_id).rules(BOOK3_AI)[trade_id]
    assert rule.exit_day == expected and alerts.sent == []
    (tmp_path / spec_path("b3-sc-v1")).unlink()  # today's file gone: the exit stays, one alert says so
    alerts = Alerts()
    [rule] = exits(tmp_path, alerts, monkeypatch, trade_id).rules(BOOK3_AI)[trade_id]
    assert rule.exit_day == expected and len(alerts.sent) == 1 and "still runs" in alerts.sent[0]


def test_a_trade_with_no_opening_record_gets_no_exit_and_an_alert(tmp_path, monkeypatch):
    decided_run(tmp_path)
    alerts = Alerts()
    assert exits(tmp_path, alerts, monkeypatch, "unknown-trade").rules(BOOK3_AI) == {}
    assert len(alerts.sent) == 1 and "no time exit is set" in alerts.sent[0]
