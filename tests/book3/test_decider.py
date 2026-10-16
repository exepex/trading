"""Story F6 criteria 1, 4-11 and F7 criterion 3, end to end through the real D2, C2, C4 (Book 3's mode, D5) and D3
path with fake accepted answers: proposals of today never trade today; picks go through C2 and C4; records carry
Book 3's fields and replay; refusals raise `DecisionRefused` before anything is written."""

import json

import pytest

from fno.book3.decider import NO_SHEET, DecisionRefused
from fno.book3.registry import parse_registry
from fno.constants import BOOK3_AI
from fno.playbook.decision_record import validate_record
from fno.playbook.decision_run import replay
from tests.book3.engine_builders import (
    COMMON_OPPORTUNITIES,
    DAY,
    OPPORTUNITY,
    PROMPT_SHA,
    FixedInputs,
    accepted,
    decider,
    decision,
    proposal,
    repository,
    sheet_for,
    spec,
    spec_document,
    validator,
)  # fmt: skip
from tests.book3.engine_builders import evaluators as book3_evaluators
from tests.decisions.builders import SAME_CODE
from tests.playbook.evaluation_builders import book_with_open

SHADOW = [{"opportunity_id": COMMON_OPPORTUNITIES[0]["opportunity_id"], "action": "take", "width": 200,
           "reason": "rich premium"}]  # fmt: skip


def records(run):
    return {p.name: json.loads(p.read_text()) for p in run.glob("*.json") if p.name != "inputs.json"}


def opportunity_record(run):
    return records(run)[OPPORTUNITY.replace(":", "_") + ".json"]


def decide(root, the_decision, **options):
    return decider(root, **options).decide(accepted(root, the_decision))


def test_a_pick_of_yesterday_s_strategy_trades_through_c2_and_c4_and_records_book3_s_fields(tmp_path):
    """Criteria 6 and 11."""
    repository(tmp_path, [spec()])
    out = decide(tmp_path, decision(trades=[OPPORTUNITY], shadow=SHADOW))
    record = opportunity_record(out.run)
    validate_record(record)
    assert record["chosen_action"] == "trade" and record["validity"]["c4"]["ok"]
    assert record["validity"]["c4"]["mode"] == "constitution"
    assert (record["strategy_id"], record["book"]) == ("b3-sc-v1", BOOK3_AI)
    assert record["served"]["book3_prompt"] == PROMPT_SHA and "constitution" in record["served"]
    assert record["reason"] == f"picked by book3_ai: pick {OPPORTUNITY}"
    assert (record["model_served"], record["common_pack_sha256"]) == ("model-x", "a" * 64)
    day_record = records(out.run)["no_trade.json"]
    validate_record(day_record)
    assert day_record["strategy_id"] is None


def test_a_proposal_registered_today_is_on_no_sheet_and_cannot_be_picked_today(tmp_path):
    """Criterion 1: proposed and picked the same day, the pick is an attempt and nothing trades."""
    repository(tmp_path)
    out = decide(tmp_path, decision(trades=["b3-new-v1:2026-11-27"], proposals=[proposal(spec("b3-new"))]))
    log = json.loads(out.files[0].read_text())
    assert [p["status"] for p in log["proposals"]] == ["registered"]
    assert log["attempted_picks"][0]["opportunity_id"] == "b3-new-v1:2026-11-27"
    assert records(out.run)["no_trade.json"]["chosen_action"] == "no trade"
    row = parse_registry((tmp_path / "book3/strategies/registry.csv").read_text())[0]
    assert (row["proposed_on"], row["model"], row["prompt_version"]) == (DAY.isoformat(), "model-x",
                                                                        "book3_decide_v1:test")  # fmt: skip


def test_a_pick_refused_by_c2_is_not_chosen_and_keeps_its_risk_reason(tmp_path):
    """Criterion 6: the open-trade limit (fixture risk manager: 3 slots) refuses the pick."""
    repository(tmp_path, [spec()])
    full = FixedInputs(the_book=book_with_open(3, name=BOOK3_AI))
    out = decider(tmp_path, inputs=full).decide(accepted(tmp_path, decision(trades=[OPPORTUNITY]), sheet_for(tmp_path)))
    record = opportunity_record(out.run)
    assert record["chosen_action"] == "no trade" and record["decision"]["reason"].startswith("slot: ")


def test_c4_blocks_a_pick_whose_constitution_no_longer_matches_d6(tmp_path):
    """Criterion 6: C4 independently of the decider; the record says blocked, nothing trades."""
    repository(tmp_path, [spec()])
    (tmp_path / "book3/constitution-v1.yaml").write_text("version: 1\n")  # damaged after registration
    out = decide(tmp_path, decision(trades=[OPPORTUNITY]))
    record = opportunity_record(out.run)
    assert record["chosen_action"] == "no trade" and "blocked by C4" in record["reason"]


def test_the_run_replays_and_a_changed_pick_in_inputs_json_is_found(tmp_path):
    """Criterion 7."""
    repository(tmp_path, [spec()])
    out = decide(tmp_path, decision(trades=[OPPORTUNITY]))
    stored = json.loads((out.run / "inputs.json").read_text())["selection"]
    evaluator = book3_evaluators().from_stored(stored)
    check = validator(tmp_path)
    assert replay(out.run, evaluator, SAME_CODE, validator=check) == []
    other = book3_evaluators().from_stored([])  # no pick: other records
    assert replay(out.run, other, SAME_CODE, validator=check) != []


@pytest.mark.parametrize("the_decision, expected", [
    ({"action": "trade"}, "exactly the keys"),
    (decision(cards=["volatility/v1/2026-10-13"]), "cards the session was not given"),
])  # fmt: skip
def test_a_bad_shape_or_an_unknown_card_is_refused_before_anything_is_written(tmp_path, the_decision, expected):
    """Criteria 5 and 8."""
    repository(tmp_path, [spec()])
    with pytest.raises(DecisionRefused, match=expected):
        decide(tmp_path, the_decision)
    assert not (tmp_path / "journal" / BOOK3_AI).exists()


def test_a_card_that_was_given_may_be_cited_and_its_role_set_is_recorded(tmp_path):
    repository(tmp_path)
    cards = {"card_ids": ["volatility/v1/2026-10-13"], "role_set_version": "volatility/v1"}
    the_decision = decision(cards=["volatility/v1/2026-10-13"], proposals=[proposal(spec("b3-new"))])
    decider(tmp_path).decide(accepted(tmp_path, the_decision, analyst_cards=cards))
    row = parse_registry((tmp_path / "book3/strategies/registry.csv").read_text())[0]
    assert row["role_set_version"] == "volatility/v1"


def test_no_sheet_or_a_sheet_that_does_not_reproduce_is_refused(tmp_path):
    """Criterion 13's decider side: the session must have seen the candidates the decision uses."""
    repository(tmp_path, [spec()])
    pack = accepted(tmp_path, decision())
    pack.private_pack.body.pop("evaluation")
    with pytest.raises(DecisionRefused, match="no day sheet"):
        decider(tmp_path).decide(pack)
    assert NO_SHEET.startswith("the private pack")
    stale = {**sheet_for(tmp_path), "opportunities": []}
    with pytest.raises(DecisionRefused, match="does not reproduce"):
        decider(tmp_path).decide(accepted(tmp_path, decision(), stale))


@pytest.mark.parametrize("specs", [(), ("b3-sc",)])
def test_zero_strategies_or_zero_picks_is_a_valid_no_trade_day(tmp_path, specs):
    """Criterion 8."""
    repository(tmp_path, [spec(s) for s in specs])
    out = decide(tmp_path, decision(reason="nothing worth trading"))
    day = records(out.run)["no_trade.json"]
    validate_record(day)
    assert day["chosen_action"] == "no trade"


def test_shadow_entries_change_nothing_in_the_real_records_and_are_written_when_c2_refuses(tmp_path):
    """Criterion 9 (an objection or card has no input path) and F7 criterion 3."""
    repository(tmp_path / "a", [spec()])
    repository(tmp_path / "b", [spec()])
    with_shadow = decide(tmp_path / "a", decision(trades=[OPPORTUNITY], shadow=SHADOW))
    without = decide(tmp_path / "b", decision(trades=[OPPORTUNITY]))
    assert _comparable(records(with_shadow.run)) == _comparable(records(without.run))
    repository(tmp_path / "c", [spec()])
    full = FixedInputs(the_book=book_with_open(3, name=BOOK3_AI))
    refused = decider(tmp_path / "c", inputs=full).decide(
        accepted(tmp_path / "c", decision(trades=[OPPORTUNITY], shadow=SHADOW), sheet_for(tmp_path / "c"))
    )
    shadow = json.loads(refused.files[1].read_text())
    assert opportunity_record(refused.run)["chosen_action"] == "no trade"
    assert shadow["entries"][0]["action"] == "take"


def _comparable(stored):
    """The records apart from what names the repository's own commit (the registry commit, and the inputs' hash that
    includes it): two repositories made in different seconds have different commit IDs."""

    def strip(record):
        header = {k: v for k, v in record["header"].items() if k not in ("registry_commit", "inputs_sha256")}
        return {**record, "header": header}

    return {name: strip(r) for name, r in stored.items()}


def test_a_pick_of_a_spec_edited_after_registration_never_trades(tmp_path):
    """Criterion 1: D5 refuses the edited spec, so it is on no sheet and the pick is only an attempt."""
    from fno.book3.registry import spec_path
    from tests.book3.builders import commit

    repository(tmp_path, [spec()])
    path = tmp_path / spec_path("b3-sc-v1")
    path.write_text(path.read_text() + "# edited\n")
    commit(tmp_path, "edit after registration")
    out = decide(tmp_path, decision(trades=[OPPORTUNITY]))
    log = json.loads(out.files[0].read_text())
    assert "edited after it" in log["excluded_strategies"]["b3-sc-v1"]
    assert log["attempted_picks"][0]["why"] == "not a built candidate today"
    assert records(out.run)["no_trade.json"]["chosen_action"] == "no trade"


def test_the_registry_row_names_the_registered_model_never_the_answer_s(tmp_path):
    """Criterion 4: the provenance comes from F1t's registered model, not from anything the session wrote."""
    repository(tmp_path)
    pack = accepted(tmp_path, decision(proposals=[proposal(spec("b3-new"))]), model_reported="what-the-model-says")
    decider(tmp_path).decide(pack)
    row = parse_registry((tmp_path / "book3/strategies/registry.csv").read_text())[0]
    assert row["model"] == "model-x"


def test_packs_read_now_that_differ_from_the_fired_ones_are_refused(tmp_path):
    """Self-review finding: the records may only name packs the decision really read."""
    from tests.book3.engine_builders import CONTEXT

    repository(tmp_path, [spec()])
    other = FixedInputs(context={**CONTEXT, "private_pack_sha256": "e" * 64})
    with pytest.raises(DecisionRefused, match="private pack read now"):
        decider(tmp_path, inputs=other).decide(accepted(tmp_path, decision()))
    assert not (tmp_path / "journal" / BOOK3_AI).exists()


def test_an_analyst_cards_item_without_its_fields_is_refused_never_read_as_no_cards(tmp_path):
    repository(tmp_path)
    with pytest.raises(DecisionRefused, match="analyst_cards must carry"):
        decider(tmp_path).decide(accepted(tmp_path, decision(), analyst_cards={"cards": []}))


def test_a_sheet_whose_terms_differ_is_refused_even_with_the_same_candidates(tmp_path):
    """Self-review finding: the whole sheet is compared, not only which opportunities had a trade."""
    repository(tmp_path, [spec()])
    sheet = sheet_for(tmp_path)
    sheet["opportunities"][0]["trade"] = {**sheet["opportunities"][0]["trade"], "width": 999}
    with pytest.raises(DecisionRefused, match="does not reproduce"):
        decider(tmp_path).decide(accepted(tmp_path, decision(trades=[OPPORTUNITY]), sheet))


def test_a_second_decision_on_the_day_is_refused_before_anything_is_written(tmp_path):
    repository(tmp_path, [spec()])
    decide(tmp_path, decision())
    runs = sorted((tmp_path / "journal" / BOOK3_AI / "decisions" / DAY.isoformat()).iterdir())
    with pytest.raises(DecisionRefused, match="decides once a day"):
        decide(tmp_path, decision(trades=[OPPORTUNITY]))
    assert sorted((tmp_path / "journal" / BOOK3_AI / "decisions" / DAY.isoformat()).iterdir()) == runs


def test_the_run_returns_every_file_it_wrote_and_names_the_decision_version(tmp_path):
    """F1t commits `DecidedRun.files` with the run: the day log, the shadow, and the registry, spec, ledger and C4 log
    when they were written; `served` names F1t's decision version (its run check)."""
    from fno.book3.registry import REGISTRY_FILE, spec_path
    from fno.research_engine.ledger import LEDGER_FILE

    repository(tmp_path, [spec()])
    (tmp_path / "book3/constitution-v1.yaml").write_text("version: 1\n")  # C4 blocks the pick: its log is written
    narrower = {**spec_document()["structure"], "widths": [200, 100]}
    the_proposal = proposal(spec("b3-new", structure=narrower))
    out = decide(tmp_path, decision(trades=[OPPORTUNITY], proposals=[the_proposal], reason="why today"))
    names = {p.relative_to(tmp_path).as_posix() for p in out.files}
    assert names == {f"journal/{BOOK3_AI}/proposals/{DAY}.json", f"journal/{BOOK3_AI}/shadow/{DAY}.json",
                     REGISTRY_FILE, LEDGER_FILE, spec_path("b3-new-v1"),
                     f"journal/{BOOK3_AI}/validity_failures.csv"}  # fmt: skip
    assert all(p.is_file() for p in out.files)
    assert json.loads(out.files[0].read_text())["reason"] == "why today"
    assert opportunity_record(out.run)["served"]["ai_decision_version"] == "book3_ai-decision-v1"


def test_an_edited_pick_in_the_stored_inputs_is_found_by_the_replay(tmp_path):
    """Criterion 7: an edit to `selection` in `inputs.json` itself (canonical bytes) is found."""
    from fno.desk.pack_items import canonical_json

    repository(tmp_path, [spec()])
    out = decide(tmp_path, decision(trades=[OPPORTUNITY]))
    path = out.run / "inputs.json"
    stored = json.loads(path.read_text())
    check = validator(tmp_path)
    path.write_bytes(canonical_json(stored))  # an unedited canonical rewrite still replays
    assert replay(out.run, book3_evaluators().from_stored(stored["selection"]), SAME_CODE, validator=check) == []
    stored["selection"] = []
    path.write_bytes(canonical_json(stored))
    assert replay(out.run, book3_evaluators().from_stored([]), SAME_CODE, validator=check) != []


def test_served_keeps_the_run_s_own_playbook_and_config_whatever_the_context_says(tmp_path):
    """DecisionRun merges an AI book's served components under its own two, which always win."""
    from fno.playbook.decision_run import DecisionRun
    from fno.playbook.decision_store import DecisionStore
    from tests.decisions.builders import CONTEXT, doc, snapshot
    from tests.playbook.evaluation_builders import Counts, FixedValues, OwnShadowBooks, chain_market, evaluator
    from tests.risk.builders import book

    context = {**CONTEXT, "served": {"playbook": "forged", "config": "forged", "extra": "kept"}}
    run = DecisionRun(evaluator(), DecisionStore(tmp_path, "book1_rules")).decide(
        DAY, snapshot(doc("sc-a")), chain_market(), FixedValues(), book(), Counts(), OwnShadowBooks(), context
    )
    served = json.loads((run / "no_trade.json").read_text())["served"]
    assert served["extra"] == "kept" and "forged" not in (served["playbook"], served["config"])
