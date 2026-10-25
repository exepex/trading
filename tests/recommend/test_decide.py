"""REC1b criteria 2, 4, 7 and 10's decision part: the closed reason order (one test per adjacent pair), "proven" is
rung 3 only, the real-money rule, and an unread source; every answer goes through the record's own rules."""

from dataclasses import replace

import pytest

from fno.recommend.codec import decode, encode
from fno.recommend.constants import (
    CandidateSourceName,
    EvidenceRung,
    NoTradeReason,
    PaperAnswer,
    RealMoneyAnswer,
    SourceState,
)
from fno.recommend.contracts import CandidateSource
from fno.recommend.decide import DayFacts, decide
from fno.recommend.refs import RecordRef
from fno.recommend.rungs import RUNG_RULE_SHA256
from tests.recommend.builders import COMPLETE, DAY, MADE_AT, candidate, evidence_of, sha

V = "school:CS1@1"
SCHOOL_DOWN = (CandidateSource(CandidateSourceName.DESK_BOOK1, SourceState.COMPLETE, None),
               CandidateSource(CandidateSourceName.SCHOOL, SourceState.UNAVAILABLE, "failed"))  # fmt: skip


def facts(rung: EvidenceRung = EvidenceRung.UNPROVEN, traded: bool = False, **changes) -> DayFacts:
    base = DayFacts(
        session=DAY, made_at=MADE_AT, code_commit="b" * 40, config_sha256=sha(7),
        inputs=(RecordRef("playbook/registry.csv", sha(8)),), versions=(evidence_of(V, rung),),
        candidates=(candidate(V, rung, traded=traded),), sources=COMPLETE, data_ok=True, step_problems=False,
        quote_gate_failed=False, weather_red=False,
    )  # fmt: skip
    return replace(base, **changes)


def decided(*args, **kwargs):
    record = decide(facts(*args, **kwargs))
    assert decode(encode(record)) == record  # every answer is a valid, readable record
    return record


def test_today_no_established_version_gives_do_not_trade_and_no_trade():
    record = decided()
    assert (record.real_money, record.paper, record.reason) == (
        RealMoneyAnswer.DO_NOT_TRADE_REAL_MONEY,
        PaperAnswer.NO_TRADE,
        NoTradeReason.NO_ESTABLISHED_VERSION,
    )


@pytest.mark.parametrize("rung", [EvidenceRung.UNPROVEN, EvidenceRung.EXPLORATORY, EvidenceRung.WATCHING])
def test_a_trade_below_rung_3_is_never_a_recommendation(rung):
    record = decided(rung, traded=True)
    assert (record.paper, record.reason) == (PaperAnswer.NO_TRADE, NoTradeReason.NO_ESTABLISHED_VERSION)


def test_a_rung_3_trade_is_the_paper_recommendation():
    record = decided(EvidenceRung.ESTABLISHED, traded=True)
    assert (record.paper, record.paper_trade.version, record.reason) == (PaperAnswer.PAPER_TRADE, V, None)


def test_an_established_version_that_did_not_trade_gives_no_candidate():
    assert decided(EvidenceRung.ESTABLISHED).reason is NoTradeReason.NO_CANDIDATE


# Criterion 2: each pair of adjacent reasons, both true: the earlier one wins.
PAIRS = [
    ({"data_ok": False, "step_problems": True}, NoTradeReason.DATA_CHECK_FAILED),
    ({"step_problems": True, "quote_gate_failed": True}, NoTradeReason.STEP_PROBLEMS),
    ({"quote_gate_failed": True, "weather_red": True}, NoTradeReason.QUOTE_GATE_FAILED),
    ({"weather_red": True, "risk_refused": {V}}, NoTradeReason.WEATHER_RED),
    ({"risk_refused": {V}, "braked": {V}}, NoTradeReason.RISK_CAP),
    ({"braked": {V}}, NoTradeReason.BRAKE),
]


@pytest.mark.parametrize(("changes", "reason"), PAIRS)
def test_the_earlier_reason_wins(changes, reason):
    assert decided(EvidenceRung.ESTABLISHED, **changes).reason is reason


def test_step_problems_come_before_no_established_version():
    assert decided(step_problems=True, quote_gate_failed=True).reason is NoTradeReason.STEP_PROBLEMS


def test_no_established_version_comes_before_the_day_s_conditions():
    assert decided(quote_gate_failed=True, weather_red=True).reason is NoTradeReason.NO_ESTABLISHED_VERSION


@pytest.mark.parametrize("changes", [{"quote_gate_failed": True}, {"weather_red": True}, {"step_problems": True}])
def test_a_day_condition_stops_even_an_established_trade(changes):
    assert decided(EvidenceRung.ESTABLISHED, traded=True, **changes).paper is PaperAnswer.NO_TRADE


def test_a_trade_that_happened_wins_over_another_version_s_refusal():
    record = decided(EvidenceRung.ESTABLISHED, traded=True, risk_refused={"school:DB1@1"})
    assert record.paper is PaperAnswer.PAPER_TRADE


def test_real_money_needs_rung_3_and_rm1():
    assert decided(EvidenceRung.ESTABLISHED, rm1_eligible={V}).eligible_version == V
    assert decided(EvidenceRung.ESTABLISHED).real_money is RealMoneyAnswer.DO_NOT_TRADE_REAL_MONEY
    for rung in (EvidenceRung.UNPROVEN, EvidenceRung.EXPLORATORY, EvidenceRung.WATCHING):
        assert decided(rung, rm1_eligible={V}).real_money is RealMoneyAnswer.DO_NOT_TRADE_REAL_MONEY


def test_a_failed_data_check_never_names_an_eligible_version():
    record = decided(EvidenceRung.ESTABLISHED, rm1_eligible={V}, data_ok=False)
    assert (record.real_money, record.reason) == (RealMoneyAnswer.DO_NOT_TRADE_REAL_MONEY,
                                                  NoTradeReason.DATA_CHECK_FAILED)  # fmt: skip


def test_an_unread_school_with_an_established_driver_is_data_check_failed():
    record = decided(EvidenceRung.ESTABLISHED, rm1_eligible={V}, candidates=(), sources=SCHOOL_DOWN)
    assert (record.reason, record.eligible_version) == (NoTradeReason.DATA_CHECK_FAILED, None)


def test_an_unread_school_changes_nothing_while_nothing_is_established():
    record = decided(candidates=(), sources=SCHOOL_DOWN)
    assert record.reason is NoTradeReason.NO_ESTABLISHED_VERSION
    assert record.candidate_sources[1].step_status == "failed"


def test_the_decision_time_is_the_evidence_cutoff_and_the_pinned_rule_is_named():
    record = decided()
    assert (record.evidence_cutoff, record.rung_rule_sha256) == (MADE_AT, RUNG_RULE_SHA256)


@pytest.mark.parametrize("rung", [EvidenceRung.UNPROVEN, EvidenceRung.EXPLORATORY, EvidenceRung.WATCHING])
def test_rm1_naming_a_version_below_rung_3_is_a_failed_data_check(rung):
    """Judge 654 S1: the two gates disagree, so nothing is trusted and nothing is eligible."""
    record = decided(rung, rm1_eligible={V})
    assert (record.real_money, record.reason, record.eligible_version) == (
        RealMoneyAnswer.DO_NOT_TRADE_REAL_MONEY,
        NoTradeReason.DATA_CHECK_FAILED,
        None,
    )


@pytest.mark.parametrize("changes", [{"step_problems": True}, {"weather_red": True}, {"quote_gate_failed": True}])
def test_a_day_condition_stops_real_money_too(changes):
    """The orchestrator's ruling on judge 654 m2: never ELIGIBLE on a day the day itself stops."""
    record = decided(EvidenceRung.ESTABLISHED, traded=True, rm1_eligible={V}, **changes)
    assert (record.real_money, record.eligible_version) == (RealMoneyAnswer.DO_NOT_TRADE_REAL_MONEY, None)
