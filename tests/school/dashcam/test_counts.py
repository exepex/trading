"""Criterion 3 (story MS-P1c): the public counts file passes the record scan and holds no strike, price or symbol."""

import csv
from dataclasses import replace
from datetime import timedelta

import pytest

from fno.composition import build_record_scanner
from fno.record_scan.record_files import NamedFiles
from fno.school.constants import REASONS_BY_OUTCOME, Outcome, RoadCode
from fno.school.contracts.dashcam import ReplayConflict
from fno.school.contracts.records import DecisionRecord
from fno.school.dashcam.counts import HEADER, PublicCountsFile, count_rows
from fno.school.dashcam.names import counts_path
from tests.school.contracts import builders as b
from tests.school.contracts.test_records import closed_record, outcome_record, trade_record

SLOT = "15:00"
RECORDS = (trade_record(), trade_record(), closed_record(), outcome_record())


def test_counts_are_per_road_driver_outcome_and_reason():
    rows = count_rows(b.SESSION, SLOT, RECORDS)
    assert rows == [
        (b.SESSION.isoformat(), SLOT, "BANKNIFTY-M", "CS1@1", "trade", "", 2),
        (b.SESSION.isoformat(), SLOT, "BANKNIFTY-M", "N0@1", "road_closed", "lot_mismatch", 1),
    ]


def test_an_empty_slot_has_a_header_only_file(tmp_path):
    file = PublicCountsFile(tmp_path).write(b.SESSION, SLOT, ())
    assert file.read_text() == ",".join(HEADER) + "\n"


def test_the_file_passes_the_record_scan_and_holds_only_codes_and_whole_numbers(tmp_path):
    file = PublicCountsFile(tmp_path).write(b.SESSION, SLOT, RECORDS)
    assert build_record_scanner().scan(list(NamedFiles([file]).records())) == []
    rows = list(csv.DictReader(file.read_text().splitlines()))
    reasons = {reason for allowed in REASONS_BY_OUTCOME.values() for reason in allowed}
    for row in rows:
        assert RoadCode(row["road"]) and Outcome(row["outcome"]) and row["reason"] in reasons
        assert row["count"].isdigit()
        assert row["driver"].replace("@", "").isalnum()
    text = file.read_text()
    trade = next(r for r in RECORDS if isinstance(r, DecisionRecord) and r.decision.proposal)
    for leg in trade.decision.proposal.legs:
        assert str(leg.key.strike) not in text and leg.key.expiry.isoformat() not in text
    for quoted in trade.witnessed:
        assert str(quoted.quote.bid) not in text and str(quoted.quote.ask) not in text
    assert str(trade.decision.proposal.net_premium) not in text and trade.snapshot_id not in text
    assert trade.card_sha256 not in text


def test_the_file_is_written_once_the_same_counts_again_are_a_no_op(tmp_path):
    counts = PublicCountsFile(tmp_path)
    file = counts.write(b.SESSION, SLOT, RECORDS)
    assert file == tmp_path / counts_path(b.SESSION, SLOT)
    counts.write(b.SESSION, SLOT, RECORDS)
    assert len(list(tmp_path.rglob("*.csv"))) == 1


def test_other_counts_for_a_written_file_are_a_replay_conflict(tmp_path):
    counts = PublicCountsFile(tmp_path)
    counts.write(b.SESSION, SLOT, RECORDS)
    changed = (*RECORDS, replace(trade_record(), slot=SLOT))
    with pytest.raises(ReplayConflict, match="rule broken"):
        counts.write(b.SESSION, SLOT, changed)


def test_records_of_another_session_or_slot_are_not_counted():
    next_day = b.SESSION + timedelta(days=1)
    other_session = replace(
        trade_record(), session=next_day, decision=replace(trade_record().decision, session=next_day)
    )
    other_slot = replace(trade_record(), slot="15:01")
    assert count_rows(b.SESSION, SLOT, [other_session, other_slot]) == []
    assert len(count_rows(b.SESSION, SLOT, [trade_record(), other_session, other_slot])) == 1


@pytest.mark.parametrize("slot", ["15:00/../x", "../15:00", "1500", "15:0", "", "15:00\n"])
def test_a_slot_that_is_not_a_time_never_reaches_a_path(slot, tmp_path):
    with pytest.raises(ValueError, match="not a slot time"):
        counts_path(b.SESSION, slot)
    with pytest.raises(ValueError):
        PublicCountsFile(tmp_path).write(b.SESSION, slot, RECORDS)
    assert not list(tmp_path.rglob("*"))
