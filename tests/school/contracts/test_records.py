"""Criterion 3 (story MS-P1a): records round-trip to identical bytes; a changed field changes the bytes."""

from dataclasses import replace
from datetime import timedelta

import pytest

from fno.school.constants import ClosureReason, NoTradeReason, Outcome, RefusalReason, RoadCode
from fno.school.contracts.accounts import FilledLeg, FillResult
from fno.school.contracts.decisions import Decision
from fno.school.contracts.records import DecisionRecord, OutcomeRecord, WitnessedQuote
from fno.school.contracts.safety import LawResult
from tests.school.contracts import builders as b

ROAD = RoadCode.BANKNIFTY_MONTHLY


def trade_record(**changes) -> DecisionRecord:
    decision = Decision("CS1@1", ROAD, b.SESSION, Outcome.TRADE, "", b.put_spread())
    record = DecisionRecord(b.SESSION, "15:00", ROAD, "ef" * 32, "fixture_20261102_150100", "ab" * 32, None, decision,
                            (LawResult("max_loss", True, None, 10_000.0, 2_500.0),),
                            (WitnessedQuote(b.key(1000.0), b.quote()),),
                            {"expected_move": 812.5, "history": 20})  # fmt: skip
    return replace(record, **changes)


def outcome_record(**changes) -> OutcomeRecord:
    when = b.SLOT_AT + timedelta(minutes=4)
    entry = FillResult((FilledLeg(b.key(1000.0), "sell", 30, 10.0, 21.4),), filled_at=when, seal_sha256="cd" * 32)
    exit_ = FillResult((FilledLeg(b.key(1000.0), "buy", 30, 4.0, 20.9),), filled_at=when, seal_sha256="cd" * 32)
    record = OutcomeRecord(
        "p1", "CS1@1", ROAD, "cd" * 32, entry, exit_, "profit_target", 180.0, 42.3, 137.7, 0.0551, -30.0
    )
    return replace(record, **changes)


@pytest.mark.parametrize("record", [trade_record(), outcome_record()], ids=["decision", "outcome"])
def test_round_trip_gives_an_equal_record_and_identical_bytes(record):
    data = record.to_bytes()
    again = type(record).from_bytes(data)
    assert again == record and again.to_bytes() == data


def test_a_closed_road_and_a_refusal_round_trip():
    closed = Decision("N0@1", ROAD, b.SESSION, Outcome.ROAD_CLOSED, ClosureReason.LOT_MISMATCH)
    record = trade_record(decision=closed, road_closed_by=ClosureReason.LOT_MISMATCH, snapshot_id="", law_results=())
    assert DecisionRecord.from_bytes(record.to_bytes()) == record
    refused = Decision("CS1@1", ROAD, b.SESSION, Outcome.REFUSED, RefusalReason.MISSING_QUOTE, b.put_spread())
    assert DecisionRecord.from_bytes(trade_record(decision=refused).to_bytes()).decision == refused


def test_ints_stay_ints_and_floats_stay_floats_in_inputs():
    record = trade_record(inputs={"history": 20, "move": 20.0, "note": "x"})
    assert DecisionRecord.from_bytes(record.to_bytes()).to_bytes() == record.to_bytes()


@pytest.mark.parametrize("change", [{"card_sha256": "00" * 32}, {"inputs": {"expected_move": 812.6, "history": 20}},
                                    {"decision": Decision("CS1@1", ROAD, b.SESSION, Outcome.NO_TRADE,
                                                          NoTradeReason.RULE_NOT_FIRED)}])  # fmt: skip
def test_a_changed_field_changes_the_bytes(change):
    assert trade_record(**change).to_bytes() != trade_record().to_bytes()


def test_the_bytes_are_sorted_compact_json():
    data = trade_record().to_bytes()
    assert b": " not in data and data.startswith(b'{"card_sha256"')


def test_not_a_number_is_refused():
    with pytest.raises(ValueError):
        trade_record(inputs={"move": float("nan")}).to_bytes()


def test_a_record_must_match_its_decision():
    with pytest.raises(ValueError):
        trade_record(road=RoadCode.NIFTY_MONTHLY)


def test_an_outcome_needs_both_fills():
    with pytest.raises(ValueError):
        outcome_record(exit=FillResult(refused=(RefusalReason.MISSING_QUOTE,)))
