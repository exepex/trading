"""Story E5, Book 1 by code alone. Criterion 1: its decision equals D2's on the same inputs, and three fixture days
replay through D3's replay. Criterion 3: without a `paper` version, each session day commits "no approved strategy".
Criterion 2 (no AI on its path) is in test_no_ai.py; criteria 4 and 5 end to end in test_book1_daily.py."""

import json
from datetime import date, datetime, time

import pytest

from fno.constants import BOOK1_RULES, NO_APPROVED_STRATEGY
from fno.models import IST
from fno.playbook.decision_run import replay
from fno.playbook.decision_store import DecisionStore
from tests.decisions.builders import SAME_CODE, doc, snapshot
from tests.playbook.evaluation_builders import Counts, FixedValues, OwnShadowBooks, chain_market
from tests.risk.builders import book

from .builders import DAYS, book1, clock_at, priced_evaluator


def FIFTEEN(day):  # noqa: N802
    return datetime.combine(day, time(15), IST)


def records(run):
    return {p.name: json.loads(p.read_text()) for p in run.glob("*.json") if p.name != "inputs.json"}


def test_book1_s_decision_is_d2_s_and_three_fixture_days_replay(tmp_path):
    playbook = snapshot(doc("sc-a"))
    decider, commits = book1(tmp_path, playbook, clock_at(FIFTEEN(DAYS[0])))
    chosen = []
    for day in DAYS:
        assert decider.decide(day).startswith(f"Book 1 {day}: decided")
        [run] = DecisionStore(tmp_path, BOOK1_RULES).runs(day)
        assert replay(run, priced_evaluator(), SAME_CODE) == []  # D3's replay, same code: the same records
        direct = priced_evaluator().evaluate(day, playbook.playbook(), chain_market(day=day), FixedValues(), book(),
                                      Counts(), OwnShadowBooks())  # fmt: skip
        day_record = records(run)["no_trade.json"]
        assert day_record["decision"]["reason"] == (
            f"chosen: {[o.opportunity.opportunity_id for o in direct.chosen]}" if direct.chosen
            else "no opportunity was chosen today")  # fmt: skip
        assert all(r["chosen_action"] == r["rule_default"] for r in records(run).values())  # the rule's action
        chosen += [o.opportunity.opportunity_id for o in direct.chosen]
    assert chosen and len(commits.made) == 3  # at least one fixture day trades; each day committed once


def test_without_a_paper_version_each_session_day_commits_no_approved_strategy(tmp_path):
    decider, commits = book1(tmp_path, snapshot(doc("cand", status="research")), clock_at(FIFTEEN(DAYS[0])))
    for day in DAYS:
        decider.decide(day)
        marker = DecisionStore(tmp_path, BOOK1_RULES).day_folder(day) / "no_approved_strategy.json"
        assert json.loads(marker.read_text())["kind"] == NO_APPROVED_STRATEGY
        assert any(marker in paths for _, _, paths, _ in commits.made)  # committed with the day's run
    assert decider.decide(date(2026, 10, 18)).endswith("not a session day, nothing decided")  # a Sunday
    assert len(commits.made) == 3


def test_a_rerun_with_the_same_inputs_decides_nothing_twice(tmp_path):
    decider, commits = book1(tmp_path, snapshot(doc("sc-a")), clock_at(FIFTEEN(DAYS[0])))
    decider.decide(DAYS[0])
    assert "already decided" in decider.decide(DAYS[0]) and len(commits.made) == 1


def test_only_the_d2_chosen_book_trades_of_a_run_that_replays_become_orders(tmp_path):
    from fno.books.book1_orders import OrdersRefused, ReplayedOrders

    from .builders import priced_evaluator

    playbook = snapshot(doc("sc-a"), doc("cand", status="research"), registered_research=("cand",))
    decider, _ = book1(tmp_path, playbook, clock_at(FIFTEEN(DAYS[0])))
    decider.decide(DAYS[0])
    [run] = DecisionStore(tmp_path, BOOK1_RULES).runs(DAYS[0])
    chosen = json.loads((run / "no_trade.json").read_text())["decision"]["reason"]
    orders = ReplayedOrders(priced_evaluator(), SAME_CODE).orders(BOOK1_RULES, run, FIFTEEN(DAYS[0]))
    assert orders and chosen == f"chosen: {[o.decision_id for o in orders]}"  # the shadow candidate is not ordered
    assert {o.strategy for o in orders} == {"sc-a-v1"}
    inputs = run / "inputs.json"
    inputs.write_bytes(inputs.read_bytes().replace(b'"spot":25000.0', b'"spot":25100.0'))  # edited after commit
    with pytest.raises(OrdersRefused, match="does not replay"):
        ReplayedOrders(priced_evaluator(), SAME_CODE).orders(BOOK1_RULES, run, FIFTEEN(DAYS[0]))


def test_a_version_approved_today_trades_from_the_next_session_so_today_has_no_approved_strategy(tmp_path):
    """Judge 84 should-fix: Book 1 reads approved_on(day), not the file's status now (an approval waits a session)."""
    from fno.playbook.decision_inputs import PlaybookSnapshot
    from fno.playbook.registry import RegistryRow, render
    from fno.playbook.schema import parse_strategy

    paper = doc("sc-a")
    sha = parse_strategy(paper).parameters_sha256
    rows = [RegistryRow("sc-a", 1, sha, "research", date(2026, 10, 6), "desk", ""),
            RegistryRow("sc-a", 1, sha, "paper", DAYS[0], "owner", "abcdef1")]  # approved on the day  # fmt: skip
    today = PlaybookSnapshot(snapshot(paper).files, render(rows), "c" * 40)
    assert today.playbook().approved() and not today.playbook().approved_on(DAYS[0])
    decider, _ = book1(tmp_path, today, clock_at(FIFTEEN(DAYS[0])))
    decider.decide(DAYS[0])
    assert (DecisionStore(tmp_path, BOOK1_RULES).day_folder(DAYS[0]) / "no_approved_strategy.json").is_file()
