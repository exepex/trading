"""REC1b's gathering: every port read once, any failure named and turned into data_check_failed, rungs from the
versions' own evidence (judge 641 m1), unavailable sources kept as unavailable, the record valid every time."""

from dataclasses import replace
from datetime import timedelta

from fno.recommend.codec import decode, encode
from fno.recommend.constants import CandidateSourceName, EvidenceRung, NoTradeReason, OutcomeSource, SourceState
from fno.recommend.decide import decide
from fno.recommend.gather import Header, Ports, gather
from fno.recommend.ports import DayConditions
from fno.recommend.rungs import ForwardOutcome
from tests.recommend.builders import DAY, ESTABLISHED, MADE_AT
from tests.recommend.fakes import CLEAR, FakeConditions, FakeEligibility, FakeEvidence, FakeSource, seen

HEADER = Header("c" * 40, "d" * 64)
CS1, DESK = "school:CS1@1", "book1_rules"
SCHOOL = (seen(CS1, True, road="#NIFTY-M"), seen(CS1, road="#BANKNIFTY-M"))


def ports(**changes) -> Ports:
    base = Ports(
        sources=(FakeSource(CandidateSourceName.DESK_BOOK1, (seen(DESK),)), FakeSource(CandidateSourceName.SCHOOL, SCHOOL)),
        evidence=FakeEvidence(rated=(CS1, DESK)), conditions=FakeConditions(), eligibility=FakeEligibility(),
    )  # fmt: skip
    return replace(base, **changes)


def recorded(**changes):
    gathered = gather(DAY, MADE_AT, HEADER, ports(**changes))
    record = decide(gathered.facts)
    assert decode(encode(record)) == record
    return gathered, record


def test_today_every_candidate_is_kept_with_rung_0_and_the_answer_is_no_established_version():
    gathered, record = recorded()
    assert gathered.problems == ()
    assert [(c.version, c.rung, c.traded) for c in record.candidates] == [
        (DESK, EvidenceRung.UNPROVEN, False),
        (CS1, EvidenceRung.UNPROVEN, False),
        (CS1, EvidenceRung.UNPROVEN, True),
    ]
    assert record.reason is NoTradeReason.NO_ESTABLISHED_VERSION


def test_the_records_read_are_the_record_s_inputs_sorted():
    _, record = recorded()
    assert [ref.path for ref in record.inputs] == sorted(ref.path for ref in record.inputs)
    assert CLEAR.used[0] in record.inputs


def test_school_off_is_unavailable_with_no_candidates_and_no_problem():
    gathered, record = recorded(sources=(FakeSource(CandidateSourceName.DESK_BOOK1, (seen(DESK),)),
                                         FakeSource(CandidateSourceName.SCHOOL, status="ok (school:OFF)")))  # fmt: skip
    school = record.candidate_sources[1]
    assert (school.state, school.step_status, gathered.problems) == (SourceState.UNAVAILABLE, "ok (school:OFF)", ())
    assert [c.version for c in record.candidates] == [DESK]
    assert record.reason is NoTradeReason.NO_ESTABLISHED_VERSION


def test_a_source_that_cannot_be_read_is_unavailable_and_the_day_is_data_check_failed():
    gathered, record = recorded(sources=(FakeSource(CandidateSourceName.DESK_BOOK1, (seen(DESK),)),
                                         FakeSource(CandidateSourceName.SCHOOL, fails="seal damaged")))  # fmt: skip
    assert record.candidate_sources[1].step_status == "input_failed"
    assert record.reason is NoTradeReason.DATA_CHECK_FAILED
    assert gathered.problems == ("candidate source school could not be read: seal damaged",)


def test_failed_evidence_conditions_each_give_data_check_failed():
    for changes in ({"evidence": FakeEvidence(fails="git failed")}, {"conditions": FakeConditions(fails="log gone")}):
        gathered, record = recorded(**changes)
        assert record.reason is NoTradeReason.DATA_CHECK_FAILED and len(gathered.problems) >= 1


def test_a_decision_of_an_unrated_version_is_a_problem_never_a_guessed_rung():
    gathered, record = recorded(evidence=FakeEvidence(rated=(DESK,)))
    assert record.reason is NoTradeReason.DATA_CHECK_FAILED
    assert all(c.version == DESK for c in record.candidates)
    assert "school:CS1@1" in gathered.problems[0]


def test_the_rung_comes_from_the_version_s_own_evidence():
    history = tuple(ForwardOutcome(CS1, DAY - timedelta(days=k), OutcomeSource.FORWARD, True,
                                   MADE_AT - timedelta(hours=1)) for k in range(1, 31))  # fmt: skip
    _, record = recorded(evidence=FakeEvidence(rated=(CS1, DESK), history=history, passed={CS1: ESTABLISHED}))
    assert {v.version: v.rung for v in record.versions}[CS1] is EvidenceRung.ESTABLISHED
    assert record.paper_trade.version == CS1  # rung 3 and traded on NIFTY-M: the one recommendation


def test_the_day_s_conditions_reach_the_decision():
    found = DayConditions(step_problems=True, quote_gate_failed=False, weather_red=False, used=())
    _, record = recorded(conditions=FakeConditions(found))
    assert record.reason is NoTradeReason.STEP_PROBLEMS
