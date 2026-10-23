"""Criteria 1 and 2 and judge 480 (story MS-P1h): a card or first counted session set after a decision makes it not
counted; a changed driver card refuses; a later card version applies only to later decisions."""

from dataclasses import replace
from datetime import timedelta

from fno.school.registration.counting import CountingRule, FirstCounted, NotCounted, RegisteredVersion
from tests.school.registration.fakes import (
    CARD_SHA,
    CHAIN,
    COMPARISON_SHA,
    SESSION,
    FakeHistory,
    FakeLookup,
    candidate,
)


def rule(history=CHAIN, lookup=None) -> CountingRule:
    return CountingRule(history, lookup or FakeLookup())


def test_a_decision_after_the_card_the_first_counted_session_and_its_version_row_counts():
    verdict = rule().verdict(candidate())
    assert verdict.counted and verdict.card_commit == "card"


def test_a_card_registered_after_the_decision_makes_that_day_not_counted():
    later = FakeHistory({"fc": (), "decision": ("fc",), "card": ("decision",)}, default=FirstCounted(SESSION, "fc"))
    verdict = rule(later).verdict(candidate())
    assert (verdict.counted, verdict.reason) == (False, NotCounted.CARD_NOT_FROZEN_BEFORE)


def test_a_card_committed_in_the_decisions_own_commit_does_not_count_it():
    verdict = rule(replace(CHAIN, cards=("decision",))).verdict(candidate())
    assert verdict.reason == NotCounted.CARD_NOT_FROZEN_BEFORE


def test_a_card_never_committed_counts_nothing():
    assert rule(replace(CHAIN, cards=())).verdict(candidate()).reason == NotCounted.CARD_NOT_FROZEN_BEFORE


def test_a_later_card_version_applies_only_to_later_decisions():
    graph = {"c1": (), "d1": ("c1",), "c2": ("d1",), "d2": ("c2",)}
    history = FakeHistory(graph, cards=("c1", "c2"), default=FirstCounted(SESSION, "c1"))
    first, second = rule(history).verdict(candidate(commit="d1")), rule(history).verdict(candidate(commit="d2"))
    assert (first.counted, first.card_commit) == (True, "c1"), "the earlier decision keeps counting under version 1"
    assert (second.counted, second.card_commit) == (True, "c2")


def test_a_changed_driver_card_sha256_refuses_counting():
    verdict = rule().verdict(candidate(card_sha256="cd" * 32))
    assert (verdict.counted, verdict.reason) == (False, NotCounted.DRIVER_CARD_CHANGED)


def test_a_version_not_registered_before_the_decision_is_not_counted():
    assert rule(lookup=FakeLookup({})).verdict(candidate()).reason == NotCounted.VERSION_NOT_REGISTERED_BEFORE


def test_the_lookup_is_asked_with_the_decisions_commit_and_session():
    lookup = FakeLookup()
    rule(lookup=lookup).verdict(candidate())
    assert lookup.asked == [("CS1@1", SESSION, "decision")]


def test_no_first_counted_session_in_the_decisions_tree_counts_nothing():
    history = replace(CHAIN, default=FirstCounted(None, None))
    assert rule(history).verdict(candidate()).reason == NotCounted.NO_FIRST_COUNTED_SESSION


def test_the_first_counted_session_itself_counts_and_the_day_before_does_not():
    assert rule().verdict(candidate(session=SESSION)).counted
    day_before = rule().verdict(candidate(session=SESSION - timedelta(days=1)))
    assert day_before.reason == NotCounted.BEFORE_FIRST_COUNTED_SESSION


def test_a_first_counted_session_written_in_the_decisions_own_commit_does_not_count_it():
    history = replace(CHAIN, default=FirstCounted(SESSION, "decision"))
    assert rule(history).verdict(candidate()).reason == NotCounted.FIRST_COUNTED_NOT_FROZEN_BEFORE


def test_a_first_counted_session_written_on_a_branch_the_decision_does_not_descend_from_is_refused():
    history = replace(CHAIN, parents={**CHAIN.parents, "elsewhere": ()}, default=FirstCounted(SESSION, "elsewhere"))
    assert rule(history).verdict(candidate()).reason == NotCounted.FIRST_COUNTED_NOT_FROZEN_BEFORE


def test_a_first_counted_session_never_written_to_git_is_refused():
    history = replace(CHAIN, default=FirstCounted(SESSION, None))
    assert rule(history).verdict(candidate()).reason == NotCounted.FIRST_COUNTED_NOT_FROZEN_BEFORE


def test_a_row_naming_another_comparison_card_than_the_version_in_force_does_not_count():
    lookup = FakeLookup({"CS1@1": RegisteredVersion(CARD_SHA, "00" * 32)})
    verdict = rule(lookup=lookup).verdict(candidate())
    assert (verdict.counted, verdict.reason, verdict.card_commit) == (
        False,
        NotCounted.COMPARISON_CARD_MISMATCH,
        "card",
    )


def test_a_row_without_a_comparison_card_hash_does_not_count():
    lookup = FakeLookup({"CS1@1": RegisteredVersion(CARD_SHA, None)})
    assert rule(lookup=lookup).verdict(candidate()).reason == NotCounted.COMPARISON_CARD_MISMATCH


def test_a_later_card_version_needs_rows_that_name_it():
    graph = {"c1": (), "d1": ("c1",), "c2": ("d1",), "d2": ("c2",)}
    history = FakeHistory(graph, cards=("c1", "c2"), card_sha256={"c1": COMPARISON_SHA, "c2": "22" * 32},
                          default=FirstCounted(SESSION, "c1"))  # fmt: skip
    first, second = rule(history).verdict(candidate(commit="d1")), rule(history).verdict(candidate(commit="d2"))
    assert first.counted, "the earlier decision still counts under version 1"
    assert (second.counted, second.reason) == (False, NotCounted.COMPARISON_CARD_MISMATCH), "no row names version 2"
    renamed = FakeLookup({"CS1@1": RegisteredVersion(CARD_SHA, "22" * 32)})
    assert rule(history, renamed).verdict(candidate(commit="d2")).counted
