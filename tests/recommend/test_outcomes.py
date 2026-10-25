"""REC1c's outcome lookup on the school's own fixtures: a trade entered on the first session and closed on the third
is found by its sealed decision's SHA-256, driver and road; open before it closes; a ticket is a ticket; another
driver's or road's outcome never matches; a damaged outcomes file fails; a traded desk candidate fails loudly."""

from dataclasses import replace

import pytest

from fno.recommend.constants import EvidenceRung
from fno.recommend.contracts import Candidate
from fno.recommend.outcomes import SealedOutcomes
from fno.recommend.ports import InputFailed
from fno.recommend.refs import RecordRef
from fno.school.constants import SLOT_1500, Outcome, RecordKind
from fno.school.fakes import FakeDashcam
from fno.school.instructor.contracts import record_sha256
from tests.school.instructor.builders import OTHER, ROAD, SESSIONS, decision_record, held_trade, outcome, refilled

FIRST, MIDDLE, LAST = SESSIONS


def lookup(dashcam) -> SealedOutcomes:
    return SealedOutcomes(dashcam, lambda a, b: [d for d in SESSIONS if a <= d <= b])


def school_candidate(dashcam, driver="CS1@1", road=ROAD, traded=True) -> Candidate:
    seal = dashcam.find(FIRST, SLOT_1500, RecordKind.DECISIONS)
    return Candidate(f"school:{driver}", EvidenceRung.UNPROVEN, RecordRef(f"{seal.path}#{road}", seal.sha256), traded)


def test_a_closed_trade_is_found_with_its_net():
    dashcam = FakeDashcam()
    record = held_trade(dashcam)
    found = lookup(dashcam).outcome(school_candidate(dashcam), FIRST, LAST)
    assert (found.net, found.is_ticket) == (record.net, False)


def test_before_its_closing_session_the_trade_is_open():
    dashcam = FakeDashcam()
    held_trade(dashcam)
    assert lookup(dashcam).outcome(school_candidate(dashcam), FIRST, MIDDLE) is None


def test_a_ticket_is_found_as_a_ticket():
    dashcam = FakeDashcam()
    held_trade(dashcam, ticket=True)
    assert lookup(dashcam).outcome(school_candidate(dashcam, traded=False), FIRST, LAST).is_ticket


@pytest.mark.parametrize(("driver", "road"), [(OTHER, ROAD), ("CS1@1", "NIFTY-M")])
def test_another_driver_or_road_never_matches(driver, road):
    dashcam = FakeDashcam()
    held_trade(dashcam)
    assert lookup(dashcam).outcome(school_candidate(dashcam, driver, road), FIRST, LAST) is None


def test_a_damaged_outcomes_file_fails_the_check():
    dashcam = FakeDashcam()
    held_trade(dashcam)
    real_read = dashcam.read

    def damaged(seal):
        if "outcomes" in seal.path:
            raise OSError("drive down")
        return real_read(seal)

    dashcam.read = damaged
    with pytest.raises(InputFailed, match="OSError"):
        lookup(dashcam).outcome(school_candidate(dashcam), FIRST, LAST)


def test_a_traded_desk_candidate_fails_loudly_and_an_untraded_one_is_none():
    desk = Candidate("book1_rules", EvidenceRung.UNPROVEN, RecordRef("journal/x.json", "ab" * 32), True)
    with pytest.raises(InputFailed, match="not built"):
        lookup(FakeDashcam()).outcome(desk, FIRST, LAST)
    assert lookup(FakeDashcam()).outcome(replace(desk, traded=False), FIRST, LAST) is None


def test_an_outcome_of_another_decision_by_the_same_driver_and_road_never_matches():
    """A later trade of the same driver on the same road rests on another sealed decision file: never this one."""
    dashcam = FakeDashcam()
    dashcam.seal(FIRST, SLOT_1500, RecordKind.DECISIONS, (decision_record(FIRST),))
    dashcam.seal(LAST, SLOT_1500, RecordKind.OUTCOMES, (outcome("11" * 32, entry_day=MIDDLE),))
    assert lookup(dashcam).outcome(school_candidate(dashcam), FIRST, LAST) is None


def test_the_latest_correction_wins():
    dashcam = FakeDashcam()
    seal = dashcam.seal(FIRST, SLOT_1500, RecordKind.DECISIONS, (decision_record(FIRST),))
    original = outcome(seal.sha256, exit_day=MIDDLE)
    corrected = refilled(original, 15.0, corrects=record_sha256(original))
    dashcam.seal(MIDDLE, SLOT_1500, RecordKind.OUTCOMES, (original,))
    dashcam.seal(LAST, SLOT_1500, RecordKind.OUTCOMES, (corrected,))
    assert original.net != corrected.net
    assert lookup(dashcam).outcome(school_candidate(dashcam), FIRST, LAST).net == corrected.net


def _two_outcomes(second):
    dashcam = FakeDashcam()
    seal = dashcam.seal(FIRST, SLOT_1500, RecordKind.DECISIONS, (decision_record(FIRST),))
    original = outcome(seal.sha256, exit_day=MIDDLE)
    dashcam.seal(MIDDLE, SLOT_1500, RecordKind.OUTCOMES, (original,))
    dashcam.seal(LAST, SLOT_1500, RecordKind.OUTCOMES, (second(original),))
    return dashcam


def test_a_correction_counted_twice_fails_the_check():
    """Judge 658 S2's plant: two live outcomes for one candidate (a 'correction' that names nothing it replaces)."""
    dashcam = _two_outcomes(lambda original: refilled(original, 15.0))
    with pytest.raises(InputFailed, match="2 live outcomes"):
        lookup(dashcam).outcome(school_candidate(dashcam), FIRST, LAST)


def test_a_correction_of_a_record_not_on_file_fails_the_check():
    dashcam = _two_outcomes(lambda original: refilled(original, 15.0, corrects="cd" * 32))
    with pytest.raises(InputFailed, match="not on file"):
        lookup(dashcam).outcome(school_candidate(dashcam), FIRST, LAST)


def test_an_open_ticket_is_known_from_its_sealed_decision():
    dashcam = FakeDashcam()
    dashcam.seal(FIRST, SLOT_1500, RecordKind.DECISIONS, (decision_record(FIRST, outcome=Outcome.TICKET),))
    cand = school_candidate(dashcam, traded=False)
    assert lookup(dashcam).ticket(cand, FIRST) and lookup(dashcam).outcome(cand, FIRST, LAST) is None


def test_a_candidate_whose_decisions_file_is_not_the_listed_one_fails():
    dashcam = FakeDashcam()
    held_trade(dashcam)
    cand = school_candidate(dashcam, traded=False)
    with pytest.raises(InputFailed, match="not the one the recommendation listed"):
        lookup(dashcam).ticket(replace(cand, decision=replace(cand.decision, sha256="cd" * 32)), FIRST)
