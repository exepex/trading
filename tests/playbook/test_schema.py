"""Story D1 criterion 1: a file missing any field, or naming an unknown feature or structure code, is refused with
the field named."""

import pytest

from fno.playbook.fields import PlaybookError
from fno.playbook.schema import EVIDENCE, TOP, parameters_sha256, parse_strategy

from .builders import DOCUMENT, document

NESTED = {
    "structure": ("code", "strikes_rule", "width_rule"),
    "live_use_rule": ("min_days", "min_agreement", "min_available"),
    "funding": ("margin_per_lot", "source", "date"),
    "exits": ("time", "profit", "loss", "event"),
    "evaluation_plan": ("expected_range", "unit", "review_dates", "pause_rules", "catastrophic_loss_rs"),
    "evidence": EVIDENCE,
}
EVERY_FIELD = [(key, None) for key in TOP] + [(section, key) for section, keys in NESTED.items() for key in keys]


def refusal(doc) -> PlaybookError:
    with pytest.raises(PlaybookError) as refused:
        parse_strategy(doc)
    return refused.value


def test_the_valid_document_loads():
    strategy = parse_strategy(document())
    assert strategy.key == ("sc-test", 1) and strategy.status == "research"
    assert strategy.live_features == ("F1_live_atm_iv_minus_rv20", "F3_live_scheduled_event_in_window")
    assert strategy.evidence.missing == list(EVIDENCE)


@pytest.mark.parametrize(("section", "key"), EVERY_FIELD)
def test_every_missing_field_is_refused_by_name(section, key):
    doc = document()
    if key is None:
        del doc[section]
    else:
        del doc[section][key]
    assert refusal(doc).field == (section if key is None else f"{section}.{key}")


def test_a_missing_condition_field_and_range_bound_are_named():
    doc = document()
    del doc["entry_conditions"][1]["threshold"]
    assert refusal(doc).field == "entry_conditions[1].threshold"
    doc = document()
    del doc["evaluation_plan"]["expected_range"]["high"]
    assert refusal(doc).field == "evaluation_plan.expected_range.high"


def test_an_unknown_field_is_refused_by_name():
    assert refusal(document(stop_loss="2x")).field == "stop_loss"


def test_an_unknown_feature_is_refused_by_name():
    doc = document()
    doc["entry_conditions"][0]["feature"] = "F9_moon_phase"
    refused = refusal(doc)
    assert refused.field == "entry_conditions[0].feature" and "F9_moon_phase" in str(refused)


def test_a_live_feature_name_is_not_a_condition_feature():
    doc = document()
    doc["entry_conditions"][0]["feature"] = "F1_live_atm_iv_minus_rv20"
    assert refusal(doc).field == "entry_conditions[0].feature"


def test_an_unknown_structure_code_is_refused_by_name():
    doc = document()
    doc["structure"]["code"] = "XX"
    refused = refusal(doc)
    assert refused.field == "structure.code" and "XX" in str(refused)


@pytest.mark.parametrize(
    ("index", "operator", "threshold", "field"),
    [
        (0, "is", True, "entry_conditions[0].operator"),  # a number feature never uses `is`
        (0, ">", "high", "entry_conditions[0].threshold"),
        (1, ">", 0, "entry_conditions[1].operator"),  # a flag feature only uses `is`
        (1, "is", 0, "entry_conditions[1].threshold"),  # 0 is not false
    ],
)
def test_operators_and_thresholds_match_the_feature_kind(index, operator, threshold, field):
    doc = document()
    doc["entry_conditions"][index].update(operator=operator, threshold=threshold)
    assert refusal(doc).field == field


@pytest.mark.parametrize(
    ("key", "value"), [("min_days", 19), ("min_agreement", 0.89), ("min_available", 0.5), ("min_agreement", 1.5)]
)
def test_the_live_use_rule_is_never_looser_than_b7(key, value):
    doc = document()
    doc["live_use_rule"][key] = value
    assert refusal(doc).field == f"live_use_rule.{key}"


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("name",), "SC Test"), (("version",), 0), (("status",), "approved"), (("funding", "margin_per_lot"), 0),
        (("funding", "date"), "soon"), (("evaluation_plan", "review_dates"), []),
        (("evidence", "test_results_commit"), "HEAD~1"), (("payer",), "  "),
    ],
)  # fmt: skip
def test_bad_values_are_refused_by_name(path, value):
    doc = document()
    target = doc
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert refusal(doc).field == ".".join(path)


def test_an_inverted_expected_range_is_refused():
    doc = document()
    doc["evaluation_plan"]["expected_range"] = {"low": 5, "high": -5}
    assert refusal(doc).field == "evaluation_plan.expected_range.low"


def test_the_fingerprint_covers_the_rule_but_not_status_or_evidence():
    base = parameters_sha256(document())
    assert parameters_sha256(document(status="paper")) == base
    assert parameters_sha256(document(evidence={**DOCUMENT["evidence"], "red_team_note": "x.md"})) == base
    changed = document()
    changed["entry_conditions"][0]["threshold"] = 0.5
    assert parameters_sha256(changed) != base
    assert parameters_sha256(document(size_rule="2 lots")) != base
