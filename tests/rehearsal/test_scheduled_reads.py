"""REH1q (pass 2's finding, 21 Oct): a scheduled read (A16b's candles, A4h's closes) is served the earliest answer the
day saved near now (a minute back to ten ahead, as before), else the latest answer of the same IST day saved before
now; never a later day's, and never one saved more than ten minutes after now (Q1-Q4). Paced reads are unchanged."""

from datetime import date, datetime, timedelta
from pathlib import Path

from fno.intraday.candle_source import FIFTEEN_MINUTES
from fno.models import IST
from fno.rehearsal.recorded_candles import RecordedCandles
from fno.rehearsal.recorded_closes import RecordedCloseList
from fno.rehearsal.serving import NEAREST, scheduled_pick
from fno.storage.receipts import Receipt, ReceiptFolder

MANIFESTS = Path(__file__).resolve().parents[2] / "research/data/manifests/groww-candles"  # the real record's
FETCHED = datetime(2026, 10, 21, 15, 33, 11, 360951, tzinfo=IST)  # the real 21 Oct fetch (its `fetched_at`)
TICK = timedelta(microseconds=1)


def at(hh, mm, ss=0, day=21):
    return datetime(2026, 10, day, hh, mm, ss, tzinfo=IST)


# Q1: the 21 Oct candles case, from the real manifest


def candle_row(now):
    source = RecordedCandles(MANIFESTS, lambda path: None, lambda: now, lambda seconds: None)
    return source._row(FIFTEEN_MINUTES, date(2026, 9, 21), date(2026, 10, 19), now)


def test_the_21_oct_candle_read_pushed_to_15_35_43_gets_the_day_s_15_33_11_answer():
    row = candle_row(at(15, 35, 43))  # 2 min 32 s after the fetch: before REH1q, "the day fetched no such answer"
    assert row is not None and datetime.fromisoformat(row["fetched_at"]) == FETCHED


def test_a_candle_read_before_the_day_s_fetch_waits_for_it_only_within_ten_minutes():
    assert datetime.fromisoformat(candle_row(at(15, 30))["fetched_at"]) == FETCHED  # 3 min ahead: as before
    assert candle_row(FETCHED - NEAREST - TICK) is None  # more than ten minutes ahead, nothing before: not recorded


# Q2: the 16:00 recheck gets 16:00's answer, never 15:40's


def closes(tmp_path, now):
    receipts = ReceiptFolder(tmp_path)
    for name, saved in (("first", at(15, 40, 3)), ("recheck", at(16, 0, 4))):
        receipts.write(Receipt(f"data/closes/2026/10/2026-10-21.{name}.raw.json", "ab", 2,
                               saved.isoformat(), "closes read", "r"))  # fmt: skip
    return RecordedCloseList(receipts, lambda path: b"{}", lambda: now, lambda seconds: None)


def test_the_recheck_gets_its_own_answer_on_time_and_late_and_the_first_read_gets_the_first(tmp_path):
    def served(now):
        return closes(tmp_path, now)._served(now, now.date())[0].split(".")[1]

    assert served(at(16, 0)) == "recheck"  # saved 4 s after the read asked: the near window, as before
    assert served(at(16, 20)) == "recheck"  # pushed 20 minutes later: the latest before now, never 15:40's
    assert served(at(15, 40)) == "first" and served(at(15, 55)) == "recheck"  # 16:00:04 is within ten minutes
    assert served(at(15, 45)) == "first"  # nothing near: the latest before now


# Q3 and Q4: never a later day's, never more than ten minutes ahead, never another day's from behind


def test_another_day_s_answer_is_never_served_from_behind_or_far_ahead():
    yesterday, tomorrow = at(16, 0, day=20), at(8, 0, day=22)
    assert scheduled_pick(at(16, 30), [(yesterday, "20 Oct"), (tomorrow, "22 Oct")]) is None
    assert scheduled_pick(at(23, 55), [(tomorrow, "22 Oct")]) is None  # 8 h ahead


def test_ahead_stays_bounded_at_ten_minutes_and_a_later_answer_never_hides_an_earlier_one():
    now = at(15, 0)
    assert scheduled_pick(now, [(now + NEAREST, "ahead")]) == (now + NEAREST, "ahead")  # the boundary itself
    assert scheduled_pick(now, [(now + NEAREST + TICK, "too far")]) is None
    earlier = at(14, 30)
    assert scheduled_pick(now, [(earlier, "before"), (now + NEAREST + TICK, "too far")]) == (earlier, "before")


def test_empty_and_a_day_with_only_later_answers_give_nothing():
    assert scheduled_pick(at(15, 0), []) is None
    assert scheduled_pick(at(9, 0), [(at(15, 33), "afternoon")]) is None


class Clock:
    def __init__(self, now):
        self.at, self.slept = now, []

    def __call__(self):
        return self.at

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.at += timedelta(seconds=seconds)


def test_a_late_read_is_served_its_recorded_bytes_at_once_and_an_early_one_waits(tmp_path):
    """Self-review M2: through `answer()`, the fallback serves the recorded raw answer with no wait; the near window
    still waits for its saved time (no answer before it existed)."""
    receipts = ReceiptFolder(tmp_path)
    receipts.write(Receipt("data/closes/2026/10/2026-10-21.recheck.raw.json", "ab", 2, at(16, 0, 4).isoformat(),
                           "closes read", "r"))  # fmt: skip
    raw = {"data/closes/2026/10/2026-10-21.recheck.raw.json": b'{"recheck": true}'}
    late, early = Clock(at(16, 20)), Clock(at(15, 59))
    assert RecordedCloseList(receipts, raw.get, late, late.sleep).answer() == ({"recheck": True}, b'{"recheck": true}')
    assert late.slept == [] and late() == at(16, 20)
    RecordedCloseList(receipts, raw.get, early, early.sleep).answer()
    assert early.slept == [64.0] and early() == at(16, 0, 4)


def test_a_first_read_pushed_past_the_recheck_s_answer_is_served_the_recheck(tmp_path):
    """Self-review M2, the stated fidelity limit: a 15:40 read pushed past 16:00:04 gets the latest answer the day
    held, the recheck's, so A4h's recheck then reads "unchanged" where the real day compared two lists. A live read at
    that moment would also have seen the later list; nothing of the real record is written."""
    assert closes(tmp_path, at(16, 5))._served(at(16, 5), date(2026, 10, 21))[0].endswith("recheck.raw.json")


def test_the_stated_limit_at_the_real_23_oct_times(tmp_path):
    """Judge 669 m1, the limit stated exactly: 23 Oct's first read saved 15:40:07, its recheck 16:00:10. A first read
    pushed to 15:41:07 still gets its own answer near it; from then to 15:50:10 the fallback serves it at once (REH1q);
    from 15:50:10 the recheck's answer is inside the ten minutes ahead (REH1g's rule) and is served after the wait."""
    receipts = ReceiptFolder(tmp_path)
    for name, saved in (("first", at(15, 40, 7, day=23)), ("recheck", at(16, 0, 10, day=23))):
        receipts.write(Receipt(f"data/closes/2026/10/2026-10-23.{name}.raw.json", "ab", 2, saved.isoformat(),
                               "closes read", "r"))  # fmt: skip
    source = RecordedCloseList(receipts, lambda path: b"{}", lambda: None, lambda seconds: None)

    def served(hh, mm, ss):
        now = at(hh, mm, ss, day=23)
        return source._served(now, now.date())[0].split(".")[1]

    assert [served(15, 41, 7), served(15, 41, 8), served(15, 50, 9)] == ["first", "first", "first"]
    assert [served(15, 50, 10), served(15, 55, 0)] == ["recheck", "recheck"]
