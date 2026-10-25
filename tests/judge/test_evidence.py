"""Story F4 design 1 (built with F5): an AI book's evidence list is 0-20 `{pack, pointer}` items with no values;
`evidence_problems` checks the shape at `seal`, `resolve` follows an RFC 6901 pointer in a pack body."""

import pytest

from fno.judge.evidence import MAX_ITEMS, MAX_POINTER_CHARS, Unresolved, evidence_problems, resolve

BODY = {"evaluation": {"rule_default": [{"opportunity_id": "sc-a-v1:2026-11-27"}]}, "a/b": {"~x": 7}}


def item(pointer="/evaluation/rule_default/0", pack="private"):
    return {"pack": pack, "pointer": pointer}


def test_an_empty_list_and_a_good_list_are_acceptable():
    assert evidence_problems([]) == []
    assert evidence_problems([item(), item("/features/F1", "common")]) == []


def test_bad_shapes_are_each_named():
    assert evidence_problems(None) == ["evidence must be a list"]
    assert evidence_problems([{"pack": "private"}]) == ["evidence[0] must have exactly the keys pack and pointer"]
    assert evidence_problems([{**item(), "value": 1}]) == ["evidence[0] must have exactly the keys pack and pointer"]
    assert evidence_problems([item(pack="drive")]) == ["evidence[0].pack must be one of common, private"]
    assert evidence_problems([item("evaluation")]) == [
        f"evidence[0].pointer must be a JSON pointer of at most {MAX_POINTER_CHARS} characters"
    ]
    assert evidence_problems([item(), item()]) == ["evidence[1] repeats an earlier item"]


def test_boundaries_twenty_items_and_three_hundred_characters():
    assert evidence_problems([item(f"/x/{n}") for n in range(MAX_ITEMS)]) == []
    assert evidence_problems([item(f"/x/{n}") for n in range(MAX_ITEMS + 1)]) == ["evidence holds 21 items, at most 20"]
    assert evidence_problems([item("/" + "a" * (MAX_POINTER_CHARS - 1))]) == []
    assert len(evidence_problems([item("/" + "a" * MAX_POINTER_CHARS)])) == 1


def test_a_non_string_pointer_is_a_problem_never_a_crash():
    assert evidence_problems([item(5), item(5)]) == [
        f"evidence[0].pointer must be a JSON pointer of at most {MAX_POINTER_CHARS} characters",
        f"evidence[1].pointer must be a JSON pointer of at most {MAX_POINTER_CHARS} characters",
        "evidence[1] repeats an earlier item",
    ]


def test_resolve_follows_keys_indices_and_escapes():
    assert resolve(BODY, "/evaluation/rule_default/0/opportunity_id") == "sc-a-v1:2026-11-27"
    assert resolve(BODY, "/a~1b/~0x") == 7
    assert resolve(BODY, "") == BODY


@pytest.mark.parametrize("pointer", ["/evaluation/rule_default/1", "/evaluation/rule_default/01", "/nope", "x"])
def test_resolve_refuses_a_pointer_that_reaches_nothing(pointer):
    with pytest.raises(Unresolved):
        resolve(BODY, pointer)


def test_an_unhashable_pack_is_a_problem_never_a_crash():
    assert evidence_problems([item(pack=["private"])]) == ["evidence[0].pack must be one of common, private"]
