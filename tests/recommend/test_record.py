"""REC1 criteria 1, 4 (contract level), 7 (the eligible version) and 11 (judge 620 S3 and 620.1): a recommendation
breaking a rule cannot be made, and the codec reads only a complete record, never filling anything in."""

import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from fno.recommend.codec import decode, encode
from fno.recommend.constants import EvidenceRung, NoTradeReason, OutcomeSource, PaperAnswer, RealMoneyAnswer
from fno.recommend.contracts import Recommendation, RecordRefused
from fno.recommend.rungs import ForwardOutcome, VersionEvidence
from tests.recommend.builders import MADE_AT, candidate, established_day, evidence_of, no_trade, paper_trade


def plain(record: Recommendation) -> dict:
    return json.loads(encode(record))


def test_a_record_reads_back_equal_with_the_same_bytes():
    for record in (no_trade(), paper_trade()):
        assert decode(encode(record)) == record
        assert encode(decode(encode(record))) == encode(record)


def test_an_empty_candidate_set_is_written_as_empty_never_left_out():
    record = no_trade(candidates=())
    assert plain(record)["candidates"] == []
    assert decode(encode(record)).candidates == ()


@pytest.mark.parametrize("name", ["candidates", "evidence_cutoff", "versions", "reason"])
def test_a_record_without_a_field_is_refused(name):
    data = plain(no_trade())
    del data[name]
    with pytest.raises(RecordRefused, match=f"lacks {name}"):
        decode(json.dumps(data).encode())


def test_an_unknown_field_is_refused():
    data = plain(no_trade()) | {"confidence": 0.7}
    with pytest.raises(RecordRefused, match="unknown fields confidence"):
        decode(json.dumps(data).encode())


@pytest.mark.parametrize(("name", "value"), [("reason", "feeling_lucky"), ("real_money", "buy"), ("paper", "maybe")])
def test_an_unknown_code_is_refused(name, value):
    data = plain(no_trade()) | {name: value}
    with pytest.raises(RecordRefused):
        decode(json.dumps(data).encode())


@pytest.mark.parametrize("data", [b"", b"not json", b"[]", b"\xff"])
def test_bytes_that_are_not_a_record_are_refused(data):
    with pytest.raises(RecordRefused):
        decode(data)


@pytest.mark.parametrize("rung", [EvidenceRung.UNPROVEN, EvidenceRung.EXPLORATORY, EvidenceRung.WATCHING])
def test_a_trade_below_rung_3_can_never_be_a_recommendation(rung):
    with pytest.raises(RecordRefused, match="paper answer"):
        paper_trade(rung)


def test_a_rung_3_trade_is_a_recommendation():
    assert paper_trade().paper is PaperAnswer.PAPER_TRADE


@pytest.mark.parametrize("changes", [
    {"reason": None}, {"paper_trade": candidate(rung=EvidenceRung.ESTABLISHED)},
    {"paper": PaperAnswer.PAPER_TRADE},
])  # fmt: skip
def test_the_paper_answer_its_trade_and_its_reason_must_agree(changes):
    with pytest.raises(RecordRefused, match="paper answer"):
        no_trade(**changes)


def test_a_recommended_trade_must_be_one_of_the_day_s_candidates_and_traded():
    record = paper_trade()
    outsider = candidate("school:DB1@1", EvidenceRung.ESTABLISHED, n=9)
    for trade in (outsider, replace(record.paper_trade, traded=False)):
        with pytest.raises(RecordRefused, match="paper answer"):
            replace(record, paper_trade=trade)


ELIGIBLE = RealMoneyAnswer.ELIGIBLE_FOR_YOUR_OWN_REVIEW


def test_only_an_established_version_can_be_eligible():
    assert established_day(real_money=ELIGIBLE, eligible_version="school:CS1@1").eligible_version == "school:CS1@1"
    for version in ("school:CS1@1", "school:N0@1", "nobody@1"):  # rung 1, rung 0, not in the evidence
        with pytest.raises(RecordRefused, match="real-money"):
            no_trade(real_money=ELIGIBLE, eligible_version=version)


def test_the_eligible_version_is_named_exactly_when_eligible():
    for changes in ({"real_money": ELIGIBLE}, {"eligible_version": "school:CS1@1"}):
        with pytest.raises(RecordRefused, match="real-money"):
            established_day(**changes)


def test_the_evidence_cutoff_is_the_decision_time():
    with pytest.raises(RecordRefused, match="evidence_cutoff"):
        no_trade(evidence_cutoff=MADE_AT + timedelta(seconds=1))


def test_a_decision_time_without_a_zone_is_refused():
    naive = datetime(2026, 11, 2, 9, 50)
    ist = MADE_AT.astimezone(timezone(timedelta(hours=5, minutes=30)))  # the same instant, another spelling
    for moment in (naive, ist):
        with pytest.raises(RecordRefused, match="UTC"):
            no_trade(made_at=moment, evidence_cutoff=moment)


def test_candidates_must_be_sorted_so_equal_days_give_equal_bytes():
    record = no_trade()
    with pytest.raises(RecordRefused, match="sorted"):
        replace(record, candidates=tuple(reversed(record.candidates)))


@pytest.mark.parametrize(("changes", "problem"), [
    ({"config_sha256": "ab"}, "SHA-256"), ({"code_commit": "HEAD"}, "commit id"),
    ({"rung_rule_sha256": "Z" * 64}, "SHA-256"),
])  # fmt: skip
def test_malformed_hashes_and_commits_are_refused(changes, problem):
    with pytest.raises(RecordRefused, match=problem):
        no_trade(**changes)


def test_a_changed_candidate_hash_changes_the_bytes():
    record = no_trade()
    changed = replace(record.candidates[0], decision=replace(record.candidates[0].decision, sha256="f" * 64))
    assert encode(replace(record, candidates=(changed, record.candidates[1]))) != encode(record)


UNPROVEN_DAY = {NoTradeReason.DATA_CHECK_FAILED, NoTradeReason.STEP_PROBLEMS, NoTradeReason.NO_ESTABLISHED_VERSION}


@pytest.mark.parametrize("reason", list(NoTradeReason))
def test_with_no_established_version_only_the_first_three_reasons_can_occur(reason):
    if reason in UNPROVEN_DAY:
        assert decode(encode(no_trade(reason=reason))).reason is reason
    else:
        with pytest.raises(RecordRefused, match="paper answer"):
            no_trade(reason=reason)


@pytest.mark.parametrize("reason", list(NoTradeReason))
def test_with_an_established_version_no_established_version_is_never_the_reason(reason):
    if reason is NoTradeReason.NO_ESTABLISHED_VERSION:
        with pytest.raises(RecordRefused, match="paper answer"):
            established_day(reason=reason)
    else:
        assert decode(encode(established_day(reason=reason))).reason is reason


def test_a_candidate_cannot_carry_a_higher_rung_than_its_evidence():
    """The reviewer's blocking case: a rung-1 version tagged established on its candidate, sent as a trade."""
    tagged = candidate("school:CS1@1", EvidenceRung.ESTABLISHED)
    with pytest.raises(RecordRefused, match="candidate's rung"):
        no_trade(versions=(evidence_of("school:CS1@1", EvidenceRung.EXPLORATORY),), candidates=(tagged,),
                 paper=PaperAnswer.PAPER_TRADE, paper_trade=tagged, reason=None)  # fmt: skip


def test_a_candidate_whose_version_has_no_evidence_is_refused():
    with pytest.raises(RecordRefused, match="candidate's rung"):
        no_trade(candidates=(candidate("school:DB1@1", EvidenceRung.UNPROVEN, n=5),))


@pytest.mark.parametrize("changes", [
    {"versions": (evidence_of("school:CS1@1", EvidenceRung.EXPLORATORY),) * 2},
    {"inputs": (no_trade().inputs[0],) * 2},
    {"candidates": (candidate("school:CS1@1", EvidenceRung.EXPLORATORY),) * 2},
])  # fmt: skip
def test_repeated_entries_are_refused(changes):
    with pytest.raises(RecordRefused, match="repeat"):
        no_trade(**changes)


@pytest.mark.parametrize(("where", "key", "value"), [
    (("candidates", 0), "confidence", 0.9), (("versions", 0), "confidence", 0.9), (("inputs", 0), "note", "x"),
    (("candidates", 0, "decision"), "note", "x"),
])  # fmt: skip
def test_an_extra_field_at_any_depth_is_refused(where, key, value):
    data = plain(no_trade())
    node = data
    for step in where:
        node = node[step]
    node[key] = value
    with pytest.raises(RecordRefused, match="canonical"):
        decode(json.dumps(data, sort_keys=True, separators=(",", ":")).encode())


@pytest.mark.parametrize(("where", "value"), [
    (("candidates", 0, "traded"), "no"), (("versions", 0, "counted_sessions"), "3"), (("versions", 0, "rung"), True),
    (("schema_version",), 1.0), (("session",), "20261102"), (("made_at",), "2026-11-02T15:20:00+05:30"),
])  # fmt: skip
def test_a_value_of_the_wrong_type_or_spelling_is_refused(where, value):
    data = plain(no_trade())
    node = data
    for step in where[:-1]:
        node = node[step]
    node[where[-1]] = value
    with pytest.raises(RecordRefused):
        decode(json.dumps(data, sort_keys=True, separators=(",", ":")).encode())


def test_whitespace_or_a_trailing_newline_is_not_canonical():
    for data in (encode(no_trade()) + b"\n", json.dumps(plain(no_trade()), sort_keys=True).encode()):
        with pytest.raises(RecordRefused, match="canonical"):
            decode(data)


def test_a_missing_nested_field_is_refused_as_a_record_problem():
    data = plain(no_trade())
    del data["candidates"][0]["traded"]
    with pytest.raises(RecordRefused, match="does not read"):
        decode(json.dumps(data, sort_keys=True, separators=(",", ":")).encode())


def test_a_receipt_time_without_a_zone_is_refused_when_made():
    with pytest.raises(ValueError, match="time zone"):
        ForwardOutcome("school:CS1@1", MADE_AT.date(), OutcomeSource.FORWARD, True, datetime(2026, 11, 2, 9, 0))


def test_a_version_s_evidence_needs_a_whole_count_and_a_rung():
    for bad in (("v", EvidenceRung.UNPROVEN, "0", None, None), ("v", 0, 0, None, None)):
        with pytest.raises(ValueError, match="whole session count"):
            VersionEvidence(*bad)
