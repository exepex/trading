"""Story F5 part 2: Book 2's decision shape. `check_decision` refuses wrong types, a reason that is not one line of
1-600 characters, an `action` that disagrees with the slots, two slots on one opportunity, a malformed evidence list,
and, with the sheet, slots that do not follow the rule default one to one or name an opportunity not on the sheet.
Standard library only, as F1t's `seal` runs it."""

import subprocess
import sys

import pytest

from fno.book2.answer import MAX_REASON_CHARS, check_decision

A, B, C = "sc-a-v1:2026-11-27", "sc-b-v1:2026-11-27", "sc-c-v1:2026-11-27"
SHEET = {"rule_default": [{"opportunity_id": A}, {"opportunity_id": B}],
         "opportunities": [{"opportunity_id": o} for o in (A, B, C)]}  # fmt: skip


def slot(default=A, action="follow_rule", opportunity_id=None, width=None, lots=None, reason="as the rule says"):
    return {"default": default, "action": action, "opportunity_id": opportunity_id, "width": width, "lots": lots,
            "reason": reason}  # fmt: skip


def decision(slots, action=None, reason="one line", evidence=()):
    if action is None:
        actions = {s["action"] for s in slots}
        action = (
            "follow_rule"
            if actions <= {"follow_rule"}
            else "trade"
            if actions & {"trade", "follow_rule"}
            else "no_trade"
        )
    return {"action": action, "reason": reason, "slots": list(slots), "evidence": list(evidence)}


def test_good_decisions_are_acceptable_with_and_without_the_sheet():
    follow = decision([slot(A), slot(B)])
    narrower = decision([slot(A, "trade", A, width=100.0, lots=1), slot(B, "no_trade")],
                        evidence=[{"pack": "private", "pointer": "/evaluation/rule_default/0"}])  # fmt: skip
    switched = decision([slot(A, "trade", C), slot(B, "follow_rule")])
    for good in (follow, narrower, switched):
        assert check_decision(good) == [] and check_decision(good, SHEET) == []


def test_an_empty_day_is_follow_rule_with_no_slots():
    assert check_decision(decision([]), {"rule_default": [], "opportunities": []}) == []
    assert check_decision(decision([], action="no_trade")) == [
        "action must be 'follow_rule' for these slots, not 'no_trade'"
    ]


def test_the_action_must_agree_with_the_slots():
    vetoed = [slot(A, "no_trade"), slot(B, "no_trade")]
    assert check_decision(decision(vetoed)) == []
    assert check_decision(decision(vetoed, action="trade")) == [
        "action must be 'no_trade' for these slots, not 'trade'"
    ]
    one_kept = [slot(A, "no_trade"), slot(B)]
    assert check_decision(decision(one_kept, action="follow_rule")) == [
        "action must be 'trade' for these slots, not 'follow_rule'"
    ]


KEYS = "the decision must have exactly the keys action, evidence, reason, slots"
SLOT_KEYS = "slots[0] must have exactly the keys action, default, lots, opportunity_id, reason, width"
ONE_LINE = f"must be one line of 1 to {MAX_REASON_CHARS} characters"
NOT_NULL = "slots[0] does not trade, so opportunity_id, width and lots must be null"
WIDTH, LOTS = (
    "slots[0].width must be a positive number or null",
    "slots[0].lots must be a whole number of at least 1, or null",
)


def trades(**terms):
    return decision([slot(action="trade", opportunity_id=A, **terms)])


@pytest.mark.parametrize("bad, problem", [
    ([], KEYS),
    ({"action": "trade", "reason": "x", "slots": []}, KEYS),
    (decision([], reason=""), f"reason {ONE_LINE}"),
    (decision([], reason="two\nlines"), f"reason {ONE_LINE}"),
    (decision([], reason="x" * (MAX_REASON_CHARS + 1)), f"reason {ONE_LINE}"),
    ({**decision([]), "slots": {}}, "slots must be a list"),
    ({**decision([]), "evidence": None}, "evidence must be a list"),
    (decision([{"default": A}], action="trade"), SLOT_KEYS),
    (decision([slot(action="buy")], action="trade"), "slots[0].action must be one of follow_rule, trade, no_trade"),
    (decision([slot(default="")]), "slots[0].default must be the rule default's opportunity ID"),
    (decision([slot(action="trade")]), "slots[0] trades, so opportunity_id must name an opportunity"),
    (decision([slot(action="no_trade", lots=1)]), NOT_NULL),
    (trades(width=0), WIDTH),
    (trades(width=True), WIDTH),
    (trades(lots=0), LOTS),
    (trades(lots=1.5), LOTS),
    (decision([slot(reason=" ")]), f"slots[0].reason {ONE_LINE}"),
])  # fmt: skip
def test_each_bad_shape_is_named(bad, problem):
    assert problem in check_decision(bad)


def test_boundary_a_reason_of_exactly_six_hundred_characters_is_acceptable():
    assert check_decision(decision([], reason="x" * MAX_REASON_CHARS)) == []


def test_two_slots_on_one_opportunity_are_refused():
    assert check_decision(decision([slot(A, "trade", C), slot(B, "trade", C)])) == [
        "two slots choose the same opportunity"
    ]


def test_with_the_sheet_the_slots_follow_the_rule_default_one_to_one():
    expected = [f"slots must follow the sheet's rule default one to one: {[A, B]}"]
    assert check_decision(decision([slot(A)]), SHEET) == expected  # one missing
    assert check_decision(decision([slot(B), slot(A)]), SHEET) == expected  # out of order
    assert check_decision(decision([slot(A), slot(B), slot(C)]), SHEET) == expected  # the AI added a trade
    assert check_decision(decision([slot(A)]), {"rule_default": [], "opportunities": []}) == [
        "slots must follow the sheet's rule default one to one: []"
    ]  # the AI can never trade when the rules offered none (D4)


def test_with_the_sheet_a_named_opportunity_must_be_on_it():
    off = decision([slot(A, "trade", "sc-z-v1:2026-11-27"), slot(B)])
    assert check_decision(off) == []
    assert check_decision(off, SHEET) == ["opportunities not on the sheet: sc-z-v1:2026-11-27"]


def test_it_imports_the_standard_library_only():
    third_party = "('yaml', 'pandas', 'numpy', 'requests')"
    code = f"import sys, fno.book2.answer; print(sorted(m for m in sys.modules if m.split('.')[0] in {third_party}))"
    assert subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True).stdout == "[]\n"
