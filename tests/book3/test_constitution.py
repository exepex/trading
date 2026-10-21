"""Story D5 criteria 3 and 6: the constitution's allowed keys and values, and a spec against it."""

import hashlib

import pytest

from fno.book3.constitution import ConstitutionError, parse_constitution
from fno.book3.spec_rules import constitution_problems, planned_holding_days
from fno.playbook.documents import strategy_from_text
from fno.playbook.fields import PlaybookError
from tests.book3.builders import constitution, constitution_bytes, spec_text


def test_the_owner_s_constitution_is_read_with_the_hash_of_its_bytes():
    raw = constitution_bytes()
    read = parse_constitution(raw, "test")
    assert len(read.structures) == 9 and read.max_holding_days == 21
    assert read.sha256 == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("changes", [
    {"risk": {"max_loss_per_trade_rs": 50_000}},  # a number in place of the reference to C2's limits
    {"scoring": "my own rules"},
    {"underlying": "BANKNIFTY"},
    {"expiry": "weekly"},
    {"structures": ["SF", "NAKED_PUT"]},
    {"max_holding_days": 30},
    {"sources": ["common_pack", "news"]},
])  # fmt: skip
def test_a_value_outside_the_owner_s_rules_is_refused(changes):
    with pytest.raises(ConstitutionError):
        constitution(**changes)


def test_a_key_outside_the_list_is_refused():
    with pytest.raises(ConstitutionError, match="keys must be exactly"):
        parse_constitution(constitution_bytes(own_limits=1), "test")


def test_a_spec_is_checked_against_the_constitution():
    rules = constitution(structures=["SC", "SF"])
    ok = strategy_from_text(spec_text(), "ok")
    assert planned_holding_days(ok) == 19 and constitution_problems(ok, rules) == []
    assert "not in the constitution" in constitution_problems(strategy_from_text(spec_text(code="BF"), "x"), rules)[0]
    with pytest.raises(PlaybookError, match="weekly"):  # D1 cannot express a weekly expiry yet; the constitution's
        strategy_from_text(spec_text(kind="weekly"), "x")  # own expiry check stays as the second guard
    long = strategy_from_text(spec_text(max_days=60), "x")  # up to 60 - 21 = 39 days held
    assert "over the constitution's 21" in constitution_problems(long, rules)[0]
