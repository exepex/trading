"""Story GB1: the branch rules. A branch goes only when nothing says it is in use."""

import sys
from datetime import UTC, datetime, timedelta

import pytest

from fno.config import ROOT

sys.path.insert(0, str(ROOT / "tools"))
from branch_rules import (  # noqa: E402
    DELETE,
    KEEP,
    KEEP_UNSURE,
    Branch,
    Evidence,
    inventory_decision,
    mentioned,
    ongoing_decision,
    parse_keep_list,
    register_branches,
)

NOW = datetime(2026, 10, 25, 12, 0, tzinfo=UTC)
OLD = NOW - timedelta(days=5)
NO_EVIDENCE = Evidence(keep_list={}, register=frozenset(), open_prs=frozenset())


def branch(name="story/x", merged=True, tip=OLD, landed=OLD, ahead=0, code=0):
    return Branch(name, "a" * 40, tip, merged, ahead, landed if merged else None, code)


def test_register_reads_only_the_branch_column():
    text = (
        "| Story | What | Owner | Branch | Files | State |\n|---|---|---|---|---|---|\n"
        "| A | mentions story/other in prose | s | story/a-code (a, c); b to come | fno/x.py | in flight |\n"
        "| B | x | s | - | fno/ai | story/not-here |\n"
    )
    found = register_branches(text)
    assert "story/a-code" in found and not found & {"story/other", "fno/x.py", "story/not-here", "in", "Branch"}


def test_keep_list_takes_names_and_reasons_and_skips_comments():
    kept = parse_keep_list("# header\nstory/a  # in flight\n\nclaude/b\n")
    assert kept == {"story/a": "in flight", "claude/b": "keep list"}


def test_mentions_match_whole_names_only():
    assert mentioned(["story/a14c", "story/a14c-part2"], "see story/a14c-part2.") == {"story/a14c-part2"}


@pytest.mark.parametrize("rule", [ongoing_decision, inventory_decision])
class TestEveryRule:
    def test_main_never_goes(self, rule):
        assert rule(branch("main"), NO_EVIDENCE, NOW)[0] == KEEP

    def test_keep_list_and_open_pr_hold_a_merged_branch(self, rule):
        held = Evidence({"story/x": "why"}, frozenset(), frozenset({"story/y"}))
        assert rule(branch("story/x"), held, NOW)[0] == KEEP
        assert rule(branch("story/y"), held, NOW)[0] == KEEP

    def test_register_holds_an_unmerged_branch_but_not_a_merged_one(self, rule):
        held = Evidence({}, frozenset({"story/x"}), frozenset())
        assert rule(branch(merged=False, ahead=2), held, NOW)[0] == KEEP
        assert rule(branch(merged=True), held, NOW)[0] == DELETE

    def test_merged_goes_after_the_grace_not_before(self, rule):
        fresh = NOW - timedelta(hours=23)
        assert rule(branch(landed=fresh), NO_EVIDENCE, NOW)[0] == KEEP_UNSURE
        assert rule(branch(tip=fresh), NO_EVIDENCE, NOW)[0] == KEEP_UNSURE  # a late push counts as activity
        assert rule(branch(landed=NOW - timedelta(hours=25)), NO_EVIDENCE, NOW)[0] == DELETE

    def test_rehearsal_runs_are_kept_for_the_owner(self, rule):
        name = "rehearsal/2026-10-19-20261018T020000Z-abc123"
        assert rule(branch(name, merged=False), NO_EVIDENCE, NOW)[0] in (KEEP, KEEP_UNSURE)


def test_standing_rule_keeps_every_unmerged_branch():
    assert ongoing_decision(branch(merged=False, ahead=3), NO_EVIDENCE, NOW)[0] == KEEP


def test_one_off_deletes_an_idle_unmerged_branch_unless_it_holds_unfinished_code_or_is_recent():
    idle = branch(merged=False, ahead=3)
    assert inventory_decision(idle, NO_EVIDENCE, NOW)[0] == DELETE
    assert inventory_decision(branch(merged=False, ahead=3, code=4), NO_EVIDENCE, NOW)[0] == KEEP_UNSURE
    assert inventory_decision(branch(merged=False, tip=NOW - timedelta(hours=47)), NO_EVIDENCE, NOW)[0] == KEEP_UNSURE
    named = Evidence({}, frozenset(), frozenset(), frozenset({"story/x"}))
    assert inventory_decision(idle, named, NOW)[0] == KEEP_UNSURE


def test_names_without_a_slash_are_matched():
    row = "| A | x | s | develop; judge-e-handover | f | st |\n"
    assert {"develop", "judge-e-handover"} <= register_branches(row)
    assert mentioned(["staging"], "pushed to staging.") == {"staging"}


def test_a_hash_inside_a_kept_name_is_not_a_comment():
    assert parse_keep_list("story/a#1  # why\n  # only a comment\n") == {"story/a#1": "why"}
