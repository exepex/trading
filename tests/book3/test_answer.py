"""Story F6 criterion 5 and F7's entry shape: Book 3's `decision` object is checked by shape alone, with the standard
library only (F1t's `seal` imports it on the routine side)."""

import subprocess
import sys

import pytest

from fno.book3.answer import MAX_REASON_CHARS, MAX_SPEC_CHARS, check_decision
from tests.book3.engine_builders import decision, proposal, spec

TAKE = {"opportunity_id": "sc-a-v1:2026-11-27", "action": "take", "width": 200, "reason": "rich premium"}
SKIP = {"opportunity_id": "sc-b-v1:2026-11-27", "action": "no_trade", "width": None, "reason": "event week"}


def good(**changes):
    return {**decision(trades=["b3-sc-v1:2026-11-27"], proposals=[proposal(spec())], shadow=[TAKE, SKIP]), **changes}


def test_a_full_answer_and_an_empty_no_trade_day_pass():
    assert check_decision(good()) == []
    assert check_decision(decision()) == []


@pytest.mark.parametrize("bad, expected", [
    ("not an object", "exactly the keys"),
    ({**decision(), "extra": 1}, "exactly the keys"),
    ({k: v for k, v in decision().items() if k != "shadow"}, "exactly the keys"),
])  # fmt: skip
def test_a_wrong_set_of_keys_is_refused_whole(bad, expected):
    problems = check_decision(bad)
    assert len(problems) == 1 and expected in problems[0]


@pytest.mark.parametrize("change, expected", [
    ({"action": "buy"}, "action must be one of"),
    ({"reason": ""}, "reason must be one line"),
    ({"reason": "two\nlines"}, "reason must be one line"),
    ({"reason": "x" * (MAX_REASON_CHARS + 1)}, "reason must be one line"),
    ({"action": "no_trade"}, "non-empty exactly when action is trade"),
    ({"trades": "b3-sc-v1"}, "trades must be a list"),
    ({"trades": [{"opportunity_id": "x"}]}, "trades[0] must have exactly the keys"),
    ({"reason": "carriage\rreturn"}, "reason must be one line"),
    ({"reason": "line\u2028separator"}, "reason must be one line"),
    ({"proposals": {"spec": "x"}}, "proposals must be a list"),
    ({"proposals": [proposal("")]}, "spec must be text, not empty"),
    ({"proposals": [proposal("x" * (MAX_SPEC_CHARS + 1))]}, f"at most {MAX_SPEC_CHARS} characters"),
    ({"proposals": [{**proposal(spec()), "supersedes": None}]}, "supersedes must be text"),
    ({"shadow": [{**TAKE, "width": None}]}, "positive number for a take"),
    ({"shadow": [{**TAKE, "width": True}]}, "positive number for a take"),
    ({"shadow": [{**TAKE, "width": 0}]}, "positive number for a take"),
    ({"shadow": [{**SKIP, "width": 200}]}, "must be null for no_trade"),
    ({"shadow": [{**TAKE, "action": "buy"}]}, "action must be one of"),
    ({"cards_used": ["volatility/v1/2026-10-13", 3]}, "cards_used must be a list of card IDs"),
    ({"cards_used": ["a", "a"]}, "cards_used must not repeat"),
])  # fmt: skip
def test_each_shape_problem_is_named(change, expected):
    assert any(expected in p for p in check_decision(good(**change))), check_decision(good(**change))


def test_a_reason_at_the_limit_passes_and_one_over_does_not():
    assert check_decision(good(reason="x" * MAX_REASON_CHARS)) == []
    assert check_decision(good(reason="x" * (MAX_REASON_CHARS + 1))) != []


def test_a_no_trade_day_needs_no_trades_and_a_trade_day_needs_some():
    assert check_decision(decision(trades=[], reason="nothing built today")) == []
    assert check_decision({**decision(trades=["x"]), "action": "no_trade"}) != []


def test_the_shape_check_imports_only_the_standard_library():
    code = "import sys, fno.book3.answer; print(' '.join(m for m in sys.modules if m.startswith('fno')))"
    loaded = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True).stdout.split()
    assert sorted(loaded) == ["fno", "fno.book3", "fno.book3.answer"]


def test_a_pick_or_shadow_entry_named_twice_is_not_a_shape_problem():
    """F6 design 3 and F7 criterion 1: the decider refuses the repeat alone (attempted, or `no_decision`)."""
    twice = [{"opportunity_id": "x", "reason": "a"}, {"opportunity_id": "x", "reason": "b"}]
    assert check_decision(good(trades=twice)) == [] and check_decision(good(shadow=[TAKE, TAKE])) == []
