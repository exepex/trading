"""REC1 criteria 1, 4 (contract level), 7 (the eligible version) and 11 (judge 620 S3 and 620.1): a recommendation
breaking a rule cannot be made, and the codec reads only a complete record, never filling anything in."""

import json
from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from fno.recommend.codec import decode, encode
from fno.recommend.constants import EvidenceRung, NoTradeReason, PaperAnswer, RealMoneyAnswer
from fno.recommend.contracts import Recommendation, RecordRefused
from tests.recommend.builders import MADE_AT, candidate, no_trade, paper_trade


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


def test_the_eligible_version_is_named_exactly_when_eligible():
    eligible = RealMoneyAnswer.ELIGIBLE_FOR_YOUR_OWN_REVIEW
    assert no_trade(real_money=eligible, eligible_version="school:CS1@1").eligible_version == "school:CS1@1"
    for changes in ({"real_money": eligible}, {"eligible_version": "school:CS1@1"}):
        with pytest.raises(RecordRefused, match="eligible_version"):
            no_trade(**changes)


def test_the_evidence_cutoff_is_the_decision_time():
    with pytest.raises(RecordRefused, match="evidence_cutoff"):
        no_trade(evidence_cutoff=MADE_AT + timedelta(seconds=1))


def test_a_decision_time_without_a_zone_is_refused():
    naive = datetime(2026, 11, 2, 9, 50)
    with pytest.raises(RecordRefused, match="time zone"):
        no_trade(made_at=naive, evidence_cutoff=naive)


def test_candidates_must_be_sorted_so_equal_days_give_equal_bytes():
    record = no_trade()
    with pytest.raises(RecordRefused, match="sorted"):
        replace(record, candidates=tuple(reversed(record.candidates)))


@pytest.mark.parametrize("changes", [{"config_sha256": "ab"}, {"code_commit": "HEAD"}, {"rung_rule_sha256": "Z" * 64}])
def test_malformed_hashes_and_commits_are_refused(changes):
    with pytest.raises(RecordRefused):
        no_trade(**changes)


def test_a_changed_candidate_hash_changes_the_bytes():
    record = no_trade()
    changed = replace(record.candidates[0], decision=replace(record.candidates[0].decision, sha256="f" * 64))
    assert encode(replace(record, candidates=(changed, record.candidates[1]))) != encode(record)


def test_every_reason_makes_a_valid_no_trade_record():
    for reason in NoTradeReason:
        assert decode(encode(no_trade(reason=reason))).reason is reason
