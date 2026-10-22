"""Criteria 1 and 2 (story MS-P1h): a card registered after a decision makes it not counted; a changed card refuses."""

from datetime import timedelta

from fno.school.registration.counting import CountingRule, NotCounted
from tests.school.registration.fakes import CARD_SHA, CHAIN, SESSION, FakeHistory, FakeLookup, candidate

FIRST = SESSION


def rule(first=FIRST, history=CHAIN, lookup=None) -> CountingRule:
    return CountingRule(first, history, lookup or FakeLookup())


def test_a_decision_after_the_card_and_its_version_row_counts():
    assert rule().verdict(candidate()).counted


def test_a_card_registered_after_the_decision_makes_that_day_not_counted():
    later = FakeHistory({"decision": (), "card": ("decision",)})  # the card's commit is a child of the decision's
    verdict = rule(history=later).verdict(candidate())
    assert (verdict.counted, verdict.reason) == (False, NotCounted.CARD_NOT_FROZEN_BEFORE)


def test_a_card_committed_in_the_decisions_own_commit_does_not_count_it():
    verdict = rule(history=FakeHistory({"decision": ()}, card_commit="decision")).verdict(candidate())
    assert verdict.reason == NotCounted.CARD_NOT_FROZEN_BEFORE


def test_a_card_never_committed_counts_nothing():
    assert rule(history=FakeHistory({}, card_commit=None)).verdict(candidate()).reason == (
        NotCounted.CARD_NOT_FROZEN_BEFORE
    )


def test_a_changed_driver_card_sha256_refuses_counting():
    verdict = rule().verdict(candidate(card_sha256="cd" * 32))
    assert (verdict.counted, verdict.reason) == (False, NotCounted.DRIVER_CARD_CHANGED)


def test_a_version_not_registered_before_the_decision_is_not_counted():
    assert rule(lookup=FakeLookup({})).verdict(candidate()).reason == NotCounted.VERSION_NOT_REGISTERED_BEFORE


def test_the_lookup_is_asked_with_the_decisions_commit_and_session():
    lookup = FakeLookup()
    rule(lookup=lookup).verdict(candidate())
    assert lookup.asked == [("CS1@1", SESSION, "decision")]


def test_no_first_counted_session_counts_nothing():
    verdict = rule(first=None).verdict(candidate())
    assert (verdict.counted, verdict.reason) == (False, NotCounted.NO_FIRST_COUNTED_SESSION)


def test_the_first_counted_session_itself_counts_and_the_day_before_does_not():
    assert rule().verdict(candidate(session=FIRST)).counted
    day_before = rule().verdict(candidate(session=FIRST - timedelta(days=1)))
    assert day_before.reason == NotCounted.BEFORE_FIRST_COUNTED_SESSION


def test_the_registered_sha_is_the_one_in_the_card_constant():
    assert candidate().card_sha256 == CARD_SHA
