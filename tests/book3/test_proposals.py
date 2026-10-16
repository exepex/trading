"""Story F6 criteria 2-4: each proposal is checked by Book 3's guards and D5's constitution, registered or refused
alone with its reason; the rule key catches a copied rule under a new name; `new_or_reused` and the provenance are set
by code, never by the answer."""

import copy

import pytest
import yaml

from fno.book3.proposals import NO_CONSTITUTION, REFUSED, REGISTERED, Book3Proposer
from fno.book3.registry import parse_registry
from fno.playbook.schema import rule_sha256
from tests.book3.builders import constitution, registry
from tests.book3.engine_builders import DAY, proposal, repository, spec, spec_document


def proposer(root, playbook=None, in_force=True, cap=10_000):
    return Book3Proposer(registry(root, today=DAY), lambda day: constitution() if in_force else None, cap,
                         lambda: dict(playbook or {}))  # fmt: skip


def register(root, *proposals, **options):
    return proposer(root, **options).register_all(DAY, list(proposals), "served-model", "book3_decide_v1:abc", "none")


def rows(root):
    return {r["strategy_id"]: r for r in parse_registry((root / "book3/strategies/registry.csv").read_text())}


def test_a_good_proposal_is_registered_new_dated_today_with_the_served_model(tmp_path):
    repository(tmp_path)
    [entry] = register(tmp_path, proposal(spec("b3-new")))
    assert (entry["status"], entry["strategy_id"], entry["new_or_reused"]) == (REGISTERED, "b3-new-v1", "new")
    row = rows(tmp_path)["b3-new-v1"]
    assert (row["proposed_on"], row["model"], row["prompt_version"], row["role_set_version"]) == (
        DAY.isoformat(), "served-model", "book3_decide_v1:abc", "none")  # fmt: skip


def _evaluation(**changes):
    plan = copy.deepcopy(spec_document()["evaluation_plan"])
    plan.update(changes)
    return plan


@pytest.mark.parametrize("changes, expected", [
    ({"status": "paper"}, "status must be research"),
    ({"evidence": {**spec_document()["evidence"], "judge_verdict": "reviews/judge/x.md"}}, "every evidence field"),
    ({"evaluation_plan": _evaluation(expected_net_per_opportunity=150)}, "expected_net_per_opportunity must be none"),
    ({"evaluation_plan": _evaluation(catastrophic_loss_rs=10_001)}, "at most the per-trade cap"),
])  # fmt: skip
def test_each_book3_guard_refuses_with_its_reason_and_registers_nothing(tmp_path, changes, expected):
    repository(tmp_path)
    [entry] = register(tmp_path, proposal(spec("b3-bad", **changes)))
    assert entry["status"] == REFUSED and expected in entry["why"] and entry["strategy_id"] is None
    assert "b3-bad-v1" not in rows(tmp_path) if (tmp_path / "book3/strategies/registry.csv").exists() else True


def test_the_cap_itself_is_accepted(tmp_path):
    repository(tmp_path)
    [entry] = register(tmp_path, proposal(spec("b3-cap", evaluation_plan=_evaluation(catastrophic_loss_rs=10_000))))
    assert entry["status"] == REGISTERED


@pytest.mark.parametrize("structure_change, expected", [
    ({"code": "XX"}, "structure"),  # D1 refuses an unknown code
    ({"expiry": {"kind": "monthly", "min_days": 30, "max_days": 45, "exit_days_before_expiry": 20}}, "over the "
                                                                                                     "constitution"),
])  # fmt: skip
def test_a_spec_breaking_d1_or_the_constitution_is_refused_and_the_day_goes_on(tmp_path, structure_change, expected):
    repository(tmp_path)
    structure = {**spec_document()["structure"], **structure_change}
    entries = register(tmp_path, proposal(spec("b3-wide", structure=structure)), proposal(spec("b3-fine")))
    assert entries[0]["status"] == REFUSED and expected in entries[0]["why"]
    assert entries[1]["status"] == REGISTERED  # one refusal never stops the others


def test_unparseable_text_and_no_constitution_are_refused(tmp_path):
    repository(tmp_path)
    assert "not valid YAML" in register(tmp_path, proposal("a: [unclosed"))[0]["why"]
    assert "YAML mapping" in register(tmp_path, proposal("- a list"))[0]["why"]
    assert register(tmp_path, proposal(spec("b3-x")), in_force=False)[0]["why"] == NO_CONSTITUTION


def test_the_same_rule_under_another_name_is_refused_even_with_new_descriptions(tmp_path):
    repository(tmp_path, [spec("b3-first")])
    copied = spec("b3-copy", payer="someone else entirely", edge_family="renamed")
    [entry] = register(tmp_path, proposal(copied))
    assert entry["status"] == REFUSED and entry["why"] == "same rule as b3-first-v1: trade that one"


def test_two_proposals_with_one_rule_on_the_same_day_register_only_the_first(tmp_path):
    repository(tmp_path)
    entries = register(tmp_path, proposal(spec("b3-one")), proposal(spec("b3-two")))
    assert [e["status"] for e in entries] == [REGISTERED, REFUSED]


def test_a_playbook_rule_copied_or_a_named_predecessor_reads_reused(tmp_path):
    repository(tmp_path, [spec("b3-old")])
    playbook_copy = spec("b3-from-book1", entry_conditions=[{"feature": "F1_atm_iv_minus_rv20", "operator": ">",
                                                             "threshold": 0}])  # fmt: skip
    playbook = {rule_sha256(yaml.safe_load(playbook_copy)): "sc-a-v1"}
    first = register(tmp_path, proposal(playbook_copy), playbook=playbook)[0]
    later = spec("b3-old", version=2, structure={**spec_document()["structure"], "widths": [200, 100]})
    second = register(tmp_path, proposal(later, supersedes="b3-old-v1"))[0]
    assert (first["new_or_reused"], second["new_or_reused"]) == ("reused", "reused")
    assert rows(tmp_path)["b3-old-v2"]["supersedes"] == "b3-old-v1"


def test_a_re_versioned_playbook_rule_has_one_rule_key():
    """Agreed with D5's owner: a version re-registered with the same rule keeps its rule key."""
    assert rule_sha256(spec_document(version=1)) == rule_sha256(spec_document(name="other", version=7))
    assert rule_sha256(spec_document()) != rule_sha256(spec_document(exits={**spec_document()["exits"], "time": "x"}))


def test_a_supersedes_that_is_not_registered_is_refused(tmp_path):
    repository(tmp_path)
    [entry] = register(tmp_path, proposal(spec("b3-x"), supersedes="b3-ghost-v1"))
    assert entry["status"] == REFUSED and "supersedes a known id" in entry["why"]
