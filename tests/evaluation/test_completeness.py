"""Story S1, criterion 2: every item has a value or an exact rule; "to be decided" is rejected. A draft of proposals
is complete but not decided; only a decided protocol can be frozen."""

import pytest

from fno.evaluation.completeness import SET_AT_FREEZE, completeness_problems, undecided_items
from fno.evaluation.protocol import REQUIRED_ITEMS, parse_protocol
from tests.evaluation.builders import DECIDED_ON, DRAFT, decided


def problems(text: str) -> list[str]:
    return completeness_problems(text, parse_protocol(text))


# The owner's decisions of 14 and 15 Oct 2026 (docs/DESK_DECISIONS.md; story S6's five items, 15 Oct); every other item
# still awaits the owner
DECIDED_BY_OWNER = (
    "uncertainty_criterion", "catastrophic_loss_strategy", "ai_cost_allocation", "reporting_per_version",
    "frozen_files", "do_nothing_benchmark", "scorecard_measures", "t_check", "missed_runs", "random_control",
)  # fmt: skip
SET_ON_FREEZE_DAY = ("do_nothing_benchmark",)  # decided, but its cash rate is set on the freeze day (judge 196)
WAITING = [key for key in REQUIRED_ITEMS if key not in DECIDED_BY_OWNER or key in SET_ON_FREEZE_DAY]


def test_the_committed_draft_is_complete_and_only_the_owner_s_decided_items_are_decided():
    protocol = parse_protocol(DRAFT)
    assert problems(DRAFT) == [] and protocol.version == 1
    assert set(protocol.items) == set(REQUIRED_ITEMS)
    assert undecided_items(protocol) == WAITING


def test_a_decided_protocol_has_nothing_left_for_the_owner():
    text = decided()
    assert problems(text) == [] and undecided_items(parse_protocol(text)) == []


@pytest.mark.parametrize("words", ["to be decided", "TBD", "To Be Determined", "undecided"])
def test_a_value_left_open_is_rejected(words):
    text = DRAFT.replace("Block length 20 trading days", f"Block length {words}", 1)
    assert any(repr(words) in p or words.lower() in p.lower() for p in problems(text))


def test_open_words_anywhere_in_the_document_are_rejected():
    text = DRAFT.replace("## Plain facts", "Some rules are to be decided later.\n\n## Plain facts")
    assert any("'to be decided'" in p for p in problems(text))


def test_a_missing_item_is_named():
    start = DRAFT.index("### `review_dates`")
    end = DRAFT.index("### `ai_cost_allocation`")
    assert problems(DRAFT[:start] + DRAFT[end:]) == ["review_dates: missing (the scheduled review dates (design 12.8))"]


def test_an_item_without_a_value_is_rejected():
    start = DRAFT.index("- **Value:** C2's drawdown brake")
    end = DRAFT.index("- **Status:**", start)
    assert problems(DRAFT[:start] + "- **Value:**\n" + DRAFT[end:]) == ["catastrophic_loss_book: no Value"]


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("- **Evidence:** some evidence", "- **Evidence:** a hunch", "evidence must be one of"),
        ("- **Status:** proposal, owner decides", "- **Status:** agreed", "status must be"),
        ("Protocol version: 1", "Protocol version: one", "no 'Protocol version: <n>' line"),
    ],
)
def test_labels_and_the_version_line_are_checked(old, new, expected):
    assert any(expected in p for p in problems(DRAFT.replace(old, new, 1)))


def test_a_duplicate_or_unknown_item_is_rejected():
    block = DRAFT[DRAFT.index("### `paper_gate`") : DRAFT.index("### `strategy_review_rule`")]
    twice = DRAFT.replace(block, block + block, 1)
    assert "paper_gate: appears more than once" in problems(twice)
    unknown = DRAFT.replace("### `paper_gate`", "### `paper_gates`", 1)
    assert "unknown item 'paper_gates'" in problems(unknown)


def test_a_wrongly_dated_decision_is_not_a_decision():
    text = decided().replace(DECIDED_ON, "decided by the owner on 20 Oct", 1)
    assert any("status must be" in p for p in problems(text))
    assert undecided_items(parse_protocol(text)) == ["common_start"]


def test_the_check_command_passes_the_draft_and_refuses_it_as_decided(capsys):
    from fno.evaluation.cli import EXIT_FAILED, _check

    assert _check(decided=False) == 0
    assert "complete" in capsys.readouterr().out
    assert _check(decided=True) == EXIT_FAILED
    assert f"not decided by the owner ({len(WAITING)})" in capsys.readouterr().out


S6_ITEMS = ("do_nothing_benchmark", "scorecard_measures", "t_check", "missed_runs", "random_control")


@pytest.mark.parametrize("key", S6_ITEMS)
def test_each_of_story_s6s_items_is_required(key):
    start = DRAFT.index(f"### `{key}`")
    without = DRAFT[:start] + DRAFT[DRAFT.index("\n### ", start + 1) + 1 :]
    assert any(key in p for p in problems(without))


def test_a_decided_item_whose_value_waits_for_the_freeze_day_is_not_decided():
    """Judge 196: a number marked "(set at the freeze)" must never be frozen as it stands."""
    text = decided()
    start = text.index("### `do_nothing_benchmark`")
    marked = text[:start] + text[start:].replace("5.5% a year", f"5.5% a year {SET_AT_FREEZE}", 1)
    assert problems(marked) == []
    assert undecided_items(parse_protocol(marked)) == ["do_nothing_benchmark"]
    assert "do_nothing_benchmark" in undecided_items(parse_protocol(DRAFT))  # the committed draft carries it
