"""Criterion 3 (story MS-P1a): records round-trip to identical bytes; a changed field changes the bytes."""

from dataclasses import replace
from datetime import timedelta

import pytest

from fno.school.constants import ClosureReason, ExitReason, NoTradeReason, Outcome, RefusalReason, RoadCode
from fno.school.contracts.accounts import FilledLeg, FillResult
from fno.school.contracts.decisions import Decision
from fno.school.contracts.records import DecisionRecord, DriftRow, ExitRecord, OutcomeRecord, WitnessedQuote
from fno.school.contracts.safety import LawResult
from fno.school.contracts.slot_file import decode_slot_file, encode_slot_file
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
    entry = FillResult((FilledLeg(b.key(1000.0), "sell", 30, 10.0, 21.4),), filled_at=when, rests_on="cd" * 32)
    exit_ = FillResult((FilledLeg(b.key(1000.0), "buy", 30, 4.0, 20.9),), filled_at=when, rests_on="cd" * 32)
    money = (180.0, 42.3, 137.7, 0.0551, -30.0)  # gross, costs, net, return on risk, slippage
    record = OutcomeRecord("p1", "CS1@1", ROAD, "cd" * 32, entry, exit_, ExitReason.PROFIT_TARGET, *money)
    return replace(record, **changes)


@pytest.mark.parametrize("record", [trade_record(), outcome_record()], ids=["decision", "outcome"])
def test_round_trip_gives_an_equal_record_and_identical_bytes(record):
    data = record.to_bytes()
    again = type(record).from_bytes(data)
    assert again == record and again.to_bytes() == data


def closed_record(reason: ClosureReason = ClosureReason.LOT_MISMATCH, by: ClosureReason | None = None):
    closed = Decision("N0@1", ROAD, b.SESSION, Outcome.ROAD_CLOSED, reason)
    return trade_record(decision=closed, road_closed_by=by or reason, snapshot_id="", snapshot_sha256="")


def test_a_closed_road_and_a_refusal_round_trip():
    record = closed_record()
    assert DecisionRecord.from_bytes(record.to_bytes()) == record
    refused = Decision("CS1@1", ROAD, b.SESSION, Outcome.REFUSED, RefusalReason.MISSING_QUOTE, b.put_spread())
    assert DecisionRecord.from_bytes(trade_record(decision=refused).to_bytes()).decision == refused


def test_ints_stay_ints_and_floats_stay_floats_in_inputs():
    record = trade_record(inputs={"history": 20, "move": 20.0, "note": "x"})
    assert DecisionRecord.from_bytes(record.to_bytes()).to_bytes() == record.to_bytes()


def test_an_int_in_a_float_field_and_minus_zero_write_as_their_equal_float():
    whole = Decision("CS1@1", ROAD, b.SESSION, Outcome.TRADE, "", b.proposal_with(net_premium=180))
    as_float = replace(whole, proposal=b.proposal_with(net_premium=180.0))
    record = trade_record(decision=whole)
    assert record.to_bytes() == trade_record(decision=as_float).to_bytes()
    assert DecisionRecord.from_bytes(record.to_bytes()).to_bytes() == record.to_bytes()
    assert trade_record(inputs={"move": -0.0}).to_bytes() == trade_record(inputs={"move": 0.0}).to_bytes()


def test_a_slot_file_holds_mixed_records_and_gives_the_same_bytes_every_time():
    exit_ = ExitRecord(b.SESSION, "15:00", "p1", "CS1@1", ROAD, ExitReason.SESSIONS_HELD, "fixture_20261102_150100")
    drift = DriftRow(b.SESSION, "p1", b.filled().legs[0], None)
    records = (trade_record(), closed_record(), exit_, outcome_record(), drift)
    data = encode_slot_file(records)
    assert data == encode_slot_file(records) and decode_slot_file(data) == records
    assert data[4:8] == bytes(4), "a zero gzip time, so a rerun gives equal bytes"


def test_a_drift_row_is_unknown_without_the_1515_price():
    leg = b.filled().legs[0]
    assert DriftRow(b.SESSION, "p1", leg, None).drift is None
    assert DriftRow(b.SESSION, "p1", leg, 10.5).drift == 0.5


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


def test_a_closed_road_is_exactly_a_road_closed_decision_with_the_same_reason():
    with pytest.raises(ValueError):
        trade_record(road_closed_by=ClosureReason.LOT_MISMATCH)  # a trade on a closed road
    with pytest.raises(ValueError):
        closed_record(ClosureReason.LOT_MISMATCH, ClosureReason.HASH_MISMATCH)
    with pytest.raises(ValueError):
        trade_record(snapshot_id="")  # an open road names its snapshot
