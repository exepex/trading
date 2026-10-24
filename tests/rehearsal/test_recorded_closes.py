"""REH1b: A4h's read in a rehearsal is NSE's answer of the day, from the record: the 15:40 read gets the first answer,
the 16:00 recheck the recheck, each once the replay clock reaches its save time; any other moment is not recorded."""

import json
from datetime import UTC, datetime, timedelta

import pytest

from fno.rehearsal.recorded_closes import RecordedAnswerMissing, RecordedCloseList
from fno.storage.receipts import Receipt, ReceiptFolder

FIRST, RECHECK = "data/closes/2026/10/2026-10-23.first.raw.json", "data/closes/2026/10/2026-10-23.recheck.raw.json"


class Clock:
    def __init__(self, at):
        self.at = at

    def __call__(self):
        return self.at

    def sleep(self, seconds):
        self.at += timedelta(seconds=seconds)


@pytest.fixture
def record(tmp_path):
    receipts = ReceiptFolder(tmp_path)
    files = {FIRST: json.dumps({"data": "first"}).encode(), RECHECK: json.dumps({"data": "recheck"}).encode()}
    for path, at in ((FIRST, "2026-10-23T10:10:09+00:00"), (RECHECK, "2026-10-23T10:30:11+00:00")):
        receipts.write(Receipt(path, "a" * 64, len(files[path]), at, "closes read", "r"))
    return receipts, files


@pytest.mark.parametrize(("asked", "answer"), [((10, 10), "first"), ((10, 30), "recheck")])  # 15:40 and 16:00 IST
def test_each_read_gets_the_answer_the_day_recorded_at_its_own_time(record, asked, answer):
    receipts, files = record
    clock = Clock(datetime(2026, 10, 23, *asked, tzinfo=UTC))
    parsed, raw = RecordedCloseList(receipts, files.get, clock, clock.sleep).answer()
    assert parsed == {"data": answer} and raw == files[FIRST if answer == "first" else RECHECK]
    assert clock() >= datetime(2026, 10, 23, *asked, 9, tzinfo=UTC)  # served once it had been saved


def test_a_moment_with_no_recorded_answer_is_not_recorded(record):
    receipts, files = record
    clock = Clock(datetime(2026, 10, 23, 8, 35, tzinfo=UTC))  # 14:05 IST
    with pytest.raises(RecordedAnswerMissing, match="rehearsal:NOT_RECORDED"):
        RecordedCloseList(receipts, files.get, clock, clock.sleep).answer()


def test_of_two_answers_near_the_read_the_first_saved_is_served(tmp_path):
    """Judge 574 minor 2: two answers within ten minutes of the read; the first saved is the one the read got."""
    receipts, early, late = ReceiptFolder(tmp_path), FIRST, FIRST.replace("first", "retry")
    files = {early: json.dumps({"data": "first"}).encode(), late: json.dumps({"data": "retry"}).encode()}
    for path, at in ((late, "2026-10-23T10:14:00+00:00"), (early, "2026-10-23T10:10:09+00:00")):
        receipts.write(Receipt(path, "a" * 64, len(files[path]), at, "closes read", "r"))
    clock = Clock(datetime(2026, 10, 23, 10, 10, tzinfo=UTC))
    parsed, _ = RecordedCloseList(receipts, files.get, clock, clock.sleep).answer()
    assert parsed == {"data": "first"} and clock() == datetime(2026, 10, 23, 10, 10, 9, tzinfo=UTC)
