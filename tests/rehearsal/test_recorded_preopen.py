"""REH1c: A22's morning capture in a rehearsal answers with the raw answer the day saved for each part, at its own
seen time, read by the live part's own reader; a moment with nothing recorded is the capture's own failure. A replay
clock is not checked against servers, and says so."""

import hashlib
from datetime import date, datetime, timedelta

import pytest

from fno.models import IST
from fno.preopen.parts import INDEX_LAST_READ_MARGIN, GrowwIndexPreopen, PartFailed, PreopenPart
from fno.rehearsal.preopen_wiring import NOT_CHECKED, RehearsalClockCheck
from fno.rehearsal.recorded_preopen import RecordedPreopenPart
from fno.storage.receipts import Receipt, ReceiptFolder

DAY = date(2026, 10, 23)
GIFT = "data/preopen/raw/2026/10/23/gift_084000.json"


class Clock:
    def __init__(self, at):
        self.at = at

    def __call__(self):
        return self.at

    def sleep(self, seconds):
        self.at += timedelta(seconds=seconds)


class LivePart(PreopenPart):
    name, window = "gift", (None, None)

    def answer(self, day):
        raise AssertionError("a rehearsal never reads live")

    def __init__(self):
        self.seen = []

    def read(self, data, day, seen_at):
        self.seen.append((data, seen_at))
        return "reading"


@pytest.fixture
def record(tmp_path):
    receipts = ReceiptFolder(tmp_path)
    receipts.write(
        Receipt(GIFT, hashlib.sha256(b"{}").hexdigest(), 2, "2026-10-23T03:10:01+00:00", "preopen record", "r")
    )
    return receipts, {GIFT: b"{}"}


def test_a_part_answers_with_the_day_s_raw_answer_at_its_own_seen_time(record):
    receipts, files = record
    live, clock = LivePart(), Clock(datetime(2026, 10, 23, 8, 39, 55, tzinfo=IST))
    answer = RecordedPreopenPart(live, receipts, files.get, clock, clock.sleep).answer(DAY)
    assert (answer.raw, answer.reading, answer.seen_at) == (b"{}", "reading", datetime(2026, 10, 23, 8, 40, tzinfo=IST))
    assert live.seen == [(b"{}", answer.seen_at)] and clock() == answer.seen_at  # the live reader, at its seen time


def test_a_moment_with_no_recorded_answer_is_the_capture_s_own_failure(record):
    receipts, files = record
    clock = Clock(datetime(2026, 10, 23, 9, 30, tzinfo=IST))
    with pytest.raises(PartFailed, match="rehearsal:NOT_RECORDED gift"):
        RecordedPreopenPart(LivePart(), receipts, files.get, clock, clock.sleep).answer(DAY)


def test_a_copy_that_differs_from_its_receipt_is_refused(record):
    """Judge 563 SF1: the bytes must hash to the receipt's SHA-256."""
    receipts, _ = record
    clock = Clock(datetime(2026, 10, 23, 8, 39, 55, tzinfo=IST))
    with pytest.raises(PartFailed, match="differs from its receipt"):
        RecordedPreopenPart(LivePart(), receipts, {GIFT: b"changed"}.get, clock, clock.sleep).answer(DAY)


def test_an_answer_more_than_ten_minutes_ahead_is_not_served(record):
    """Judge 563's note: the window's upper bound."""
    receipts, files = record
    clock = Clock(datetime(2026, 10, 23, 8, 29, 59, tzinfo=IST))  # 10 min 1 s before the 08:40:00 answer
    with pytest.raises(PartFailed, match="rehearsal:NOT_RECORDED"):
        RecordedPreopenPart(LivePart(), receipts, files.get, clock, clock.sleep).answer(DAY)


def test_a_replay_clock_is_not_checked_and_says_so():
    reading = RehearsalClockCheck().check()
    assert reading.status == "clock_unchecked" and reading.warning() == NOT_CHECKED


def test_a_replayed_part_keeps_the_live_parts_read_plan(tmp_path):
    """A22e: an index part's last read is 15 s before its close live, so the replay's is too."""
    live = GrowwIndexPreopen("banknifty", source=None)
    replay = RecordedPreopenPart(live, ReceiptFolder(tmp_path), lambda path: None, lambda: None, lambda s: None)
    assert (replay.window, replay.last_read_margin) == (live.window, INDEX_LAST_READ_MARGIN)
