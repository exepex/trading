"""REC1b, criterion 10's record part (orchestrator's ruling, 25 Oct): each candidate source is complete or unavailable
with its step status, never an empty complete list; an unavailable source holding a rung-3 version makes the paper
answer data_check_failed and can name no eligible version."""

import json

import pytest

from fno.recommend.codec import decode, encode
from fno.recommend.constants import CandidateSourceName, EvidenceRung, NoTradeReason, RealMoneyAnswer, SourceState
from fno.recommend.contracts import CandidateSource, RecordRefused, source_of
from tests.recommend.builders import COMPLETE, candidate, established_day, evidence_of, no_trade

SCHOOL_DOWN = (CandidateSource(CandidateSourceName.DESK_BOOK1, SourceState.COMPLETE, None),
               CandidateSource(CandidateSourceName.SCHOOL, SourceState.UNAVAILABLE, "not_live"))  # fmt: skip


def test_an_unavailable_school_is_recorded_with_its_status_and_no_school_candidates():
    record = no_trade(candidates=(), candidate_sources=SCHOOL_DOWN)
    assert decode(encode(record)).candidate_sources[1].step_status == "not_live"


def test_a_school_candidate_from_an_unavailable_school_is_refused():
    with pytest.raises(RecordRefused, match="unavailable source"):
        no_trade(candidate_sources=SCHOOL_DOWN)


@pytest.mark.parametrize("status", [None, ""])
def test_an_unavailable_source_must_name_its_step_status(status):
    with pytest.raises(RecordRefused, match="step status"):
        CandidateSource(CandidateSourceName.SCHOOL, SourceState.UNAVAILABLE, status)


def test_a_complete_source_names_no_step_status():
    with pytest.raises(RecordRefused, match="step status"):
        CandidateSource(CandidateSourceName.SCHOOL, SourceState.COMPLETE, "failed")


@pytest.mark.parametrize("sources", [(), COMPLETE[:1], COMPLETE[::-1], COMPLETE + COMPLETE[:1]])
def test_every_source_is_listed_once_in_order(sources):
    with pytest.raises(RecordRefused, match="one entry per candidate source"):
        no_trade(candidate_sources=sources)


def test_a_record_without_its_sources_is_refused():
    data = json.loads(encode(no_trade()))
    del data["candidate_sources"]
    with pytest.raises(RecordRefused, match="lacks candidate_sources"):
        decode(json.dumps(data, sort_keys=True, separators=(",", ":")).encode())


def test_an_established_version_in_an_unavailable_source_forces_data_check_failed():
    """A recommendation cannot rest on decisions it could not read."""
    unread = {"candidates": (), "candidate_sources": SCHOOL_DOWN}
    assert established_day(reason=NoTradeReason.DATA_CHECK_FAILED, **unread).reason is NoTradeReason.DATA_CHECK_FAILED
    for reason in set(NoTradeReason) - {NoTradeReason.DATA_CHECK_FAILED}:
        with pytest.raises(RecordRefused, match="paper answer"):
            established_day(reason=reason, **unread)


def test_no_eligible_version_from_an_unavailable_source():
    with pytest.raises(RecordRefused, match="real-money"):
        established_day(candidates=(), candidate_sources=SCHOOL_DOWN, reason=NoTradeReason.DATA_CHECK_FAILED,
                        real_money=RealMoneyAnswer.ELIGIBLE_FOR_YOUR_OWN_REVIEW, eligible_version="school:CS1@1")  # fmt: skip


def test_while_nothing_is_established_an_unavailable_school_changes_no_answer():
    record = no_trade(candidates=(), candidate_sources=SCHOOL_DOWN)
    assert (record.real_money, record.reason) == (RealMoneyAnswer.DO_NOT_TRADE_REAL_MONEY,
                                                  NoTradeReason.NO_ESTABLISHED_VERSION)  # fmt: skip


def test_a_desk_version_belongs_to_the_desk_and_a_school_driver_to_the_school():
    assert source_of("book1_rules") is CandidateSourceName.DESK_BOOK1
    assert source_of("b0-monthly-sc@1") is CandidateSourceName.DESK_BOOK1
    assert source_of("school:CS1@1") is CandidateSourceName.SCHOOL


def test_a_desk_candidate_is_kept_when_only_the_school_is_unavailable():
    desk = candidate("book1_rules", EvidenceRung.UNPROVEN, traded=False, n=4)
    record = no_trade(versions=(evidence_of("book1_rules"),), candidates=(desk,), candidate_sources=SCHOOL_DOWN)
    assert decode(encode(record)).candidates == (desk,)
