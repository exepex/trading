"""Story F5 criteria 3, 5, 11, 13 and 15: Book 2's decider. Each envelope action end to end on a fake answer
(`follow_rule` trades the default; `no_trade` nothing; `choose_width` and `reduce_lots` the rebuilt candidate;
`choose_strategy` another eligible version; shadow-only takes the default and keeps the choice; forbidden is blocked
by C4 with the attempt), a blocking judge, the unproven limit, the refusals, every record valid with its label."""

import json
import time

import pytest

from fno.ai_trading.ports import DecisionRefused
from fno.book2.day_log import log_path
from fno.playbook.decision_record import validate_record
from tests.playbook.evaluation_builders import DAY, Counts

from .decider_builders import ALL_ALLOWED, FixedInputs, P, R, accepted, decider, decision, repository, sheet_for, slot


def run(tmp_path, slots, actions=None, inputs=None, **changes):
    root = repository(tmp_path, actions=actions)
    out = decider(root, inputs=inputs).decide(accepted(decision(slots), **changes))
    return root, out, {p.name: json.loads(p.read_text()) for p in out.run.glob("*.json") if p.name != "inputs.json"}


def chosen(records):
    """The trades the account takes: D3 keeps a C4-blocked trade's D2 outcome and records "no trade" as its action."""
    return {r["opportunity_id"]: r for r in records.values() if r["chosen_action"] == "trade" and r["opportunity_id"]
            != "no_trade"}  # fmt: skip


def day_log(root):
    return json.loads((root / log_path(DAY)).read_text())


def test_follow_rule_trades_both_defaults_labelled_research_and_every_record_is_valid(tmp_path):
    root, out, records = run(tmp_path, [slot(P), slot(R)])
    trades = chosen(records)
    assert set(trades) == {P, R} and all(validate_record(r) is None for r in records.values())
    assert {r["served"]["strategy_status"] for r in trades.values()} == {"research"}  # one research pick labels all
    assert (trades[P]["structure"]["width"], trades[P]["structure"]["lots"]) == (50, 2)
    assert {s["status"] for s in day_log(root)["slots"]} == {"allowed"} and out.files[0].name == f"{DAY}.json"


def test_no_trade_trades_nothing_and_keeps_both_vetoes(tmp_path):
    root, _, records = run(tmp_path, [slot(P, "no_trade"), slot(R, "no_trade")])
    assert chosen(records) == {} and [s["pick"] for s in day_log(root)["slots"]] == [None, None]


def test_choose_width_and_reduce_lots_trade_the_rebuilt_candidate(tmp_path):
    _, _, records = run(tmp_path, [slot(P, "trade", P, lots=1), slot(R, "trade", R, width=50)])
    trades = chosen(records)
    assert (trades[P]["structure"]["width"], trades[P]["structure"]["lots"]) == (50, 1)
    assert (trades[R]["structure"]["width"], trades[R]["structure"]["lots"]) == (50, 1)


def test_choose_strategy_trades_another_eligible_version_labelled_passed(tmp_path):
    _, _, records = run(tmp_path, [slot(P, "no_trade"), slot(R, "trade", P)])
    trades = chosen(records)
    assert set(trades) == {P} and trades[P]["served"]["strategy_status"] == "paper"


def test_a_shadow_only_choice_makes_the_account_take_the_default_and_keeps_the_choice(tmp_path):
    actions = {**ALL_ALLOWED, "choose_width": "shadow-only"}
    root, _, records = run(tmp_path, [slot(P), slot(R, "trade", R, width=50)], actions=actions)
    assert chosen(records)[R]["structure"]["width"] == 100  # the rule default, not the AI's 50
    shadow = day_log(root)["slots"][1]
    assert shadow["status"] == "shadow-only" and shadow["shadow"] == {"version": ["sc-r", 1], "width": 50.0, "lots": 1}


def test_a_forbidden_choice_is_blocked_by_c4_with_the_attempt(tmp_path):
    actions = {**ALL_ALLOWED, "choose_width": "forbidden"}
    root, _, records = run(tmp_path, [slot(P), slot(R, "trade", R, width=50)], actions=actions)
    blocked = next(r for r in records.values() if r["opportunity_id"] == R)
    assert blocked["chosen_action"] == "no trade" and "blocked by C4" in json.dumps(blocked)
    assert day_log(root)["slots"][1]["status"] == "forbidden" and set(chosen(records)) == {P}


def test_a_blocking_judge_holds_no_chosen_trade_and_keeps_the_rule_default_as_a_shadow(tmp_path):
    root, _, records = run(tmp_path, [slot(P), slot(R)], judge_blocks=True)
    assert chosen(records) == {} and all(r["judge"] for r in records.values())
    assert [d["opportunity_id"] for d in day_log(root)["judge_blocked_rule_default"]] == [P, R]


def test_the_unproven_limit_holds_a_version_with_an_open_trade_back(tmp_path):
    """Criterion 13: one open Book 2 trade and fewer than 20 completed: D2 does not offer it, so nothing is chosen."""
    held = FixedInputs(counts=Counts(completed=0, open_=1))
    sheet = sheet_for(inputs=held)
    assert sheet["rule_default"] == [] and {o["reason"][:9] for o in sheet["opportunities"]} == {"unproven:"}
    _, _, records = run(tmp_path, [], inputs=held, sheet=sheet)
    assert chosen(records) == {}


def test_a_foreign_sheet_and_a_missing_sheet_are_refused(tmp_path):
    root = repository(tmp_path)
    with pytest.raises(DecisionRefused, match="slots must follow"):
        decider(root).decide(accepted(decision([slot(P), slot(R)]), sheet={"rule_default": [], "opportunities": []}))
    no_sheet = accepted(decision([slot(P), slot(R)]))
    no_sheet.private_pack.body.pop("evaluation")
    with pytest.raises(DecisionRefused, match="no day sheet"):
        decider(root).decide(no_sheet)


def test_a_sheet_that_no_longer_reproduces_is_refused(tmp_path):
    root = repository(tmp_path)
    stale = sheet_for()
    stale["opportunities"][0]["reason"] = "rank 9: edited"
    with pytest.raises(DecisionRefused, match="opportunities differs"):
        decider(root).decide(accepted(decision([slot(P), slot(R)]), sheet=stale))


def test_packs_other_than_the_fired_ones_are_refused(tmp_path):
    root = repository(tmp_path)
    other = FixedInputs(context={**FixedInputs().context, "private_pack_sha256": "9" * 64})
    with pytest.raises(DecisionRefused, match="private pack read now"):
        decider(root, inputs=other).decide(accepted(decision([slot(P), slot(R)])))


def test_a_second_decision_the_same_day_is_refused(tmp_path):
    root, _, _ = run(tmp_path, [slot(P), slot(R)])
    with pytest.raises(DecisionRefused, match="decides once a day"):
        decider(root).decide(accepted(decision([slot(P), slot(R)])))


def test_a_chosen_record_without_its_strategy_status_is_refused_by_book2_itself(tmp_path, monkeypatch):
    """Criterion 15, before F1t's check: the run's served block lost `strategy_status`."""
    root = repository(tmp_path)
    book2 = decider(root)
    real = book2._context

    def unlabelled(*arguments):
        context = real(*arguments)
        return {**context, "served": {k: v for k, v in context["served"].items() if k != "strategy_status"}}

    monkeypatch.setattr(book2, "_context", unlabelled)
    with pytest.raises(DecisionRefused, match="strategy_status"):
        book2.decide(accepted(decision([slot(P), slot(R)])))


def test_decide_takes_at_most_thirty_seconds_on_the_test_day(tmp_path):
    started = time.perf_counter()
    run(tmp_path, [slot(P), slot(R, "trade", R, width=50)])
    elapsed = time.perf_counter() - started
    print(f"Book 2 decide() on the test day: {elapsed:.3f} s")
    assert elapsed < 30


def test_with_no_tradable_version_book2_writes_the_day_s_no_trade_record(tmp_path):
    """Criterion 6: an empty playbook view gives an empty sheet, no slot, and D3's day record "no trade"."""
    root = repository(tmp_path)  # the envelopes exist; Book 2 has no tradable version today
    out = decider(root, docs=()).decide(accepted(decision([]), sheet=sheet_for(docs=())))
    [day_record] = [json.loads(p.read_text()) for p in out.run.glob("no_trade*.json")]
    assert (day_record["chosen_action"], day_record["rule_default"]) == ("no trade", "no trade")
    assert day_record["authority_check"] == "the rules offered no trade: nothing to check"
