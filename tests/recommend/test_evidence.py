"""REC1b's evidence: the rated versions, and a school session counted only when MS-P1h's rule counts a sealed
decision on an open road, timed by GitHub's push receipt (unknown: not counted); nothing before the first counted
session; the desk's paper versions fail loudly until their reader exists."""

from dataclasses import dataclass
from datetime import timedelta

import pytest

from fno.recommend.evidence import NoEligibility, RecommenderEvidence
from fno.recommend.ports import InputFailed
from fno.school.constants import SLOT_1500, Outcome, RecordKind
from fno.school.fakes import FakeDashcam
from fno.school.registration.counting import CountVerdict, NotCounted
from tests.school.instructor.builders import SESSIONS, at, closed_record, decision_record

FIRST, SECOND, DAY = SESSIONS
RECEIPT = at(FIRST, 10)


@dataclass
class FakeCounting:
    refused: tuple = ()  # driver ids the rule does not count

    def verdict(self, candidate) -> CountVerdict:
        if candidate.driver_id in self.refused:
            return CountVerdict(False, NotCounted.DRIVER_CARD_CHANGED)
        return CountVerdict(True, None, "card-commit")


def evidence(dashcam=None, first=FIRST, counting=None, receipt=RECEIPT, school=("school:CS1@1",), paper=()):
    def between(a, b):
        return [d for d in SESSIONS if a <= d <= b]

    return RecommenderEvidence(lambda: school, lambda: paper, first, between, dashcam or FakeDashcam(),
                               counting or FakeCounting(), lambda commit: receipt)  # fmt: skip


def sealed(day, *records) -> FakeDashcam:
    dashcam = FakeDashcam()
    dashcam.seal(day, SLOT_1500, RecordKind.DECISIONS, records)
    return dashcam


def test_the_rated_versions_are_the_desk_book_and_the_school_rows():
    assert evidence(school=("school:REF@1", "school:CS1@1", "book2_hybrid")).versions(DAY) == (
        "book1_rules",
        "school:CS1@1",
        "school:REF@1",
    )


def test_a_desk_version_at_paper_fails_loudly():
    with pytest.raises(InputFailed, match="not built"):
        evidence(paper=("b0-monthly-sc@1",)).versions(DAY)


def test_a_counted_decision_on_an_open_road_is_a_forward_session_with_its_receipt():
    found = evidence(sealed(FIRST, decision_record(FIRST))).outcomes(DAY, at(DAY))
    assert [(o.version, o.session, o.counted, o.receipt_at) for o in found] == [("school:CS1@1", FIRST, True, RECEIPT)]


def test_a_no_trade_decision_is_a_session_too():
    found = evidence(sealed(FIRST, decision_record(FIRST, outcome=Outcome.NO_TRADE))).outcomes(DAY, at(DAY))
    assert found[0].counted


def test_a_closed_road_or_a_refused_count_is_not_counted():
    assert not evidence(sealed(FIRST, closed_record(FIRST))).outcomes(DAY, at(DAY))[0].counted
    refused = evidence(sealed(FIRST, decision_record(FIRST)), counting=FakeCounting(("CS1@1",)))
    assert not refused.outcomes(DAY, at(DAY))[0].counted


def test_an_unknown_receipt_is_kept_as_unknown():
    assert evidence(sealed(FIRST, decision_record(FIRST)), receipt=None).outcomes(DAY, at(DAY))[0].receipt_at is None


@pytest.mark.parametrize("first", [None, DAY, DAY + timedelta(days=1)])
def test_nothing_counts_before_the_first_counted_session(first):
    assert evidence(sealed(FIRST, decision_record(FIRST)), first=first).outcomes(DAY, at(DAY)) == ()


def test_the_decision_day_itself_is_never_read():
    dashcam = sealed(DAY, decision_record(DAY))
    assert evidence(dashcam).outcomes(DAY, at(DAY, 30)) == ()


def test_a_session_without_a_seal_adds_nothing():
    assert evidence(FakeDashcam()).outcomes(DAY, at(DAY)) == ()


def test_a_damaged_seal_is_an_input_failure():
    dashcam = sealed(FIRST, decision_record(FIRST))
    dashcam.files[(FIRST, SLOT_1500, RecordKind.DECISIONS)] = b"changed"
    real = dashcam.find(FIRST, SLOT_1500, RecordKind.DECISIONS)
    dashcam.find = lambda *_: real.__class__(real.path, "0" * 64, real.pushed_at, real.commit)
    with pytest.raises(InputFailed):
        evidence(dashcam).outcomes(DAY, at(DAY))


def test_no_report_and_no_eligibility_exist_yet():
    assert evidence().reports("school:CS1@1").refs() == []
    assert NoEligibility().eligible(DAY) == frozenset()
