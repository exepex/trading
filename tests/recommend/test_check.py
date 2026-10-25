"""REC1c criterion 12 and its amendment's (b), (c): every listed candidate reported and summed, a traded candidate
open until its sealed outcome exists, a ticket never counted as a trade, an unavailable source never a full total,
an unreadable outcome a failure, never a smaller total (the dropped-loser plant)."""

from datetime import date

import pytest

from fno.recommend.check import FoundOutcome, OutcomeLookup, check
from fno.recommend.check_record import CandidateState, CheckRecord, Verdict
from fno.recommend.constants import CandidateSourceName, SourceState
from fno.recommend.contracts import CandidateSource, RecordRefused
from fno.recommend.ports import InputFailed
from tests.recommend.builders import MADE_AT, candidate, evidence_of, no_trade

CHECKED = date(2026, 11, 20)
CS1, DB1, N0 = "school:CS1@1", "school:DB1@1", "school:N0@1"


class Outcomes(OutcomeLookup):
    def __init__(self, found: dict, fails: str = "", tickets: tuple = ()):
        self.found, self.fails, self.tickets = found, fails, tickets

    def ticket(self, cand, session):
        return cand.version in self.tickets

    def outcome(self, cand, session, until):
        if self.fails and cand.version == self.fails:
            raise InputFailed(f"{cand.decision.path}: damaged")
        return self.found.get(cand.version)


def day(*candidates, sources=None):
    versions = tuple(evidence_of(v) for v in sorted({c.version for c in candidates}))
    return no_trade(versions=versions, candidates=tuple(sorted(candidates, key=lambda c: (c.version, c.decision.path))),
                    **({"candidate_sources": sources} if sources else {}))  # fmt: skip


def checked(record, outcomes) -> CheckRecord:
    return check(record, "ab" * 32, CHECKED, MADE_AT, outcomes, last_check=False)


def test_every_listed_candidate_is_reported_and_the_closed_ones_summed():
    record = day(candidate(CS1, n=1), candidate(DB1, n=2), candidate(N0, traded=False, n=3))
    result = checked(record, Outcomes({CS1: FoundOutcome(1200.5, False), DB1: FoundOutcome(-3400.0, False)}))
    assert [(r.version, r.state, r.net) for r in result.results] == [
        (CS1, CandidateState.CLOSED, 1200.5),
        (DB1, CandidateState.CLOSED, -3400.0),
        (N0, CandidateState.NO_TRADE, None),
    ]
    assert (result.closed_so_far, result.open_positions, result.verdict) == (-2199.5, 0, Verdict.COMPLETE)


def test_a_traded_candidate_without_its_outcome_keeps_the_day_not_known():
    result = checked(day(candidate(CS1, n=1), candidate(DB1, n=2)), Outcomes({CS1: FoundOutcome(500.0, False)}))
    assert (result.open_positions, result.verdict, result.closed_so_far) == (1, Verdict.NOT_KNOWN_YET, 500.0)


def test_a_ticket_is_reported_apart_never_as_a_trade():
    result = checked(day(candidate(CS1, traded=False, n=1)), Outcomes({CS1: FoundOutcome(-700.0, True)}))
    assert (result.results[0].state, result.results[0].net, result.closed_so_far) == (CandidateState.TICKET, -700.0, 0)


def test_an_unavailable_source_with_an_open_trade_is_checked_again_and_then_incomplete():
    """Judge 658 S3: `incomplete` is final only once the listed candidates have closed."""
    sources = (CandidateSource(CandidateSourceName.DESK_BOOK1, SourceState.COMPLETE, None),
               CandidateSource(CandidateSourceName.SCHOOL, SourceState.UNAVAILABLE, "ok, school:OFF"))  # fmt: skip
    record = day(candidate("book1_rules", traded=True, n=4), sources=sources)
    lookup = Outcomes({})
    lookup.outcome = lambda cand, session, until: None  # the desk trade has not closed yet
    assert checked(record, lookup).verdict is Verdict.NOT_KNOWN_YET


def test_a_trade_still_open_at_the_last_check_is_never_closed():
    record = day(candidate(CS1, n=1))
    result = check(record, "ab" * 32, CHECKED, MADE_AT, Outcomes({}), last_check=True)
    assert (result.verdict, result.problem) == (Verdict.DATA_CHECK_FAILED, "never closed in 60 sessions")


def test_the_last_check_of_a_closed_day_is_simply_final():
    result = check(day(candidate(CS1, n=1)), "ab" * 32, CHECKED, MADE_AT, Outcomes({CS1: FoundOutcome(5.0, False)}),
                   last_check=True)  # fmt: skip
    assert (result.verdict, result.problem) == (Verdict.COMPLETE, "")


def test_an_unavailable_source_is_never_a_full_total():
    sources = (CandidateSource(CandidateSourceName.DESK_BOOK1, SourceState.COMPLETE, None),
               CandidateSource(CandidateSourceName.SCHOOL, SourceState.UNAVAILABLE, "ok, school:OFF"))  # fmt: skip
    result = checked(day(candidate("book1_rules", traded=False, n=4), sources=sources), Outcomes({}))
    assert (result.verdict, result.unavailable_sources) == (Verdict.INCOMPLETE, ("school",))


def test_an_unreadable_outcome_fails_the_check_never_a_smaller_total():
    """The dropped-loser plant: the losing candidate's outcome cannot be read; the check must not total the rest."""
    record = day(candidate(CS1, n=1), candidate(DB1, n=2))
    with pytest.raises(InputFailed, match="damaged"):
        checked(record, Outcomes({CS1: FoundOutcome(900.0, False), DB1: FoundOutcome(-5000.0, False)}, fails=DB1))


def test_no_candidates_is_a_complete_empty_day():
    result = checked(day(), Outcomes({}))
    assert (result.results, result.closed_so_far, result.verdict) == ((), 0, Verdict.COMPLETE)


@pytest.mark.parametrize("change", [
    {"closed_so_far": 1.0}, {"open_positions": 1}, {"verdict": Verdict.COMPLETE, "unavailable_sources": ("school",)},
    {"checked_on": date(2026, 11, 1)},
])  # fmt: skip
def test_a_check_record_whose_parts_disagree_is_refused(change):
    from dataclasses import replace

    good = checked(day(candidate(CS1, n=1)), Outcomes({CS1: FoundOutcome(10.0, False)}))
    with pytest.raises(RecordRefused):
        replace(good, **change)


def test_a_check_reads_back_with_the_same_bytes():
    good = checked(day(candidate(CS1, n=1)), Outcomes({CS1: FoundOutcome(10.0, False)}))
    assert CheckRecord.from_bytes(good.to_bytes()) == good


def test_an_open_ticket_keeps_the_day_open_so_it_is_reported_once_closed():
    """Self-review 4: an untraded ticket decision with no outcome yet is open, never 'no trade'."""
    record = day(candidate(CS1, traded=False, n=1))
    result = checked(record, Outcomes({}, tickets=(CS1,)))
    assert (result.results[0].state, result.verdict) == (CandidateState.OPEN, Verdict.NOT_KNOWN_YET)


def test_an_untraded_decision_with_a_trade_s_outcome_fails_the_check():
    """Self-review 5: the records disagree, so the check fails rather than say abstaining cost nothing."""
    with pytest.raises(InputFailed, match="untraded decision has a trade's outcome"):
        checked(day(candidate(CS1, traded=False, n=1)), Outcomes({CS1: FoundOutcome(-5000.0, False)}))
