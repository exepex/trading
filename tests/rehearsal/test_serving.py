"""REH1g (DRY2's gap G4). A scheduled read (closes, candles) is served the answer the day saved from a minute before
now to ten minutes after it. A paced read (cues, pre-open) is served the day's copy nearest to now within a minute
either side, never the same copy twice nor an older one, and only once the replay clock reaches its saved time.
An answer saved before now is no look-ahead. Each rule in one place."""

import hashlib
from datetime import date, datetime, timedelta

import pytest

from fno.models import IST
from fno.preopen.parts import LAST_READ_MARGIN, PartFailed
from fno.rehearsal.recorded_cues import RecordedCueSession
from fno.rehearsal.recorded_preopen import RecordedPreopenPart
from fno.rehearsal.serving import AROUND, EARLIER, NEAREST, ServedOnce, is_near
from fno.storage.receipts import Receipt, ReceiptFolder

READ = datetime(2026, 10, 23, 8, 50, 40, 136560, tzinfo=IST)  # the rehearsal's KOSPI read
KOSPI_SAVED = datetime(2026, 10, 23, 8, 50, 34, 20913, tzinfo=IST)  # the day's copy
KOSPI_URL = "https://query1.finance.yahoo.com/v8/finance/chart/%5EKS11?range=1d&interval=5m"
KOSPI_PATH = "yahoo/preopen/2026/10/23/085034_kospi_5m.json"
SECOND = timedelta(seconds=1)
TICK = timedelta(microseconds=1)


class Clock:
    def __init__(self, at):
        self.at = at

    def __call__(self):
        return self.at

    def sleep(self, seconds):
        self.at += timedelta(seconds=seconds)


def test_the_kospi_copy_saved_six_seconds_before_the_read_is_served():
    assert is_near(READ, KOSPI_SAVED)
    assert ServedOnce().pick(READ, [(KOSPI_SAVED, KOSPI_PATH)]) == (KOSPI_SAVED, KOSPI_PATH)


def test_a_scheduled_read_s_window_is_a_minute_before_to_ten_minutes_after_and_no_wider():
    assert timedelta(seconds=60) == EARLIER and timedelta(minutes=10) == NEAREST
    assert is_near(READ, READ - EARLIER) and is_near(READ, READ + NEAREST)
    assert not is_near(READ, READ - EARLIER - TICK)
    assert not is_near(READ, READ + NEAREST + TICK)


def test_a_paced_read_s_window_is_a_minute_either_side_and_no_wider():
    assert timedelta(seconds=60) == AROUND
    for saved in (READ - AROUND, READ + AROUND):
        assert ServedOnce().pick(READ, [(saved, "copy")]) == (saved, "copy")
    for saved in (READ - AROUND - TICK, READ + AROUND + TICK):
        assert ServedOnce().pick(READ, [(saved, "copy")]) is None


def test_the_nearest_copy_is_served_not_the_earliest():
    copies = [(READ - 50 * SECOND, "early"), (READ + 10 * SECOND, "near"), (READ + 40 * SECOND, "late")]
    assert ServedOnce().pick(READ, copies) == (READ + 10 * SECOND, "near")
    tied = [(READ + 5 * SECOND, "after"), (READ - 5 * SECOND, "before")]
    assert ServedOnce().pick(READ, tied) == (READ - 5 * SECOND, "before")  # equally near: the one already saved


def test_a_copy_is_never_served_twice():
    served, copies = ServedOnce(), [(READ, "first"), (READ + 30 * SECOND, "second")]
    assert served.pick(READ, copies)[1] == "first"
    assert served.pick(READ + 30 * SECOND, copies)[1] == "second"
    assert served.pick(READ + 30 * SECOND, copies) is None


def test_the_kospi_read_is_served_and_a_second_read_of_the_url_is_not_recorded(tmp_path):
    data = b'{"chart": {}}'
    row = f"{KOSPI_SAVED.isoformat()},{KOSPI_PATH},{KOSPI_URL},,{hashlib.sha256(data).hexdigest()},{len(data)}\n"
    (tmp_path / "kospi_preopen.csv").write_text("fetched_at,path,url,form,sha256,size_bytes\n" + row)
    clock = Clock(READ)
    session = RecordedCueSession(tmp_path, {KOSPI_PATH: data}.get, clock, clock.sleep)
    assert session.get(KOSPI_URL).content == data and clock() == READ  # saved before now: no wait
    with pytest.raises(Exception, match="rehearsal:NOT_RECORDED"):
        session.get(KOSPI_URL)


class GiftPart:
    name, window, last_read_margin = "gift", (None, None), LAST_READ_MARGIN

    def read(self, data, day, seen_at):
        return data


def test_a_pre_open_retry_gets_the_day_s_next_answer_after_waiting_for_its_seen_time(tmp_path):
    """The day saved 08:40:01 and 08:40:31; reads at 08:40:00 and 08:40:30 get one each, each at its own seen time."""
    receipts, files = ReceiptFolder(tmp_path), {}
    for stamp in ("084001", "084031"):
        path, raw = f"data/preopen/raw/2026/10/23/gift_{stamp}.json", stamp.encode()
        receipts.write(Receipt(path, hashlib.sha256(raw).hexdigest(), 6, "2026-10-23T03:11:00+00:00", "p", "r"))
        files[path] = raw
    clock = Clock(datetime(2026, 10, 23, 8, 40, tzinfo=IST))
    part = RecordedPreopenPart(GiftPart(), receipts, files.get, clock, clock.sleep)
    first = part.answer(date(2026, 10, 23))
    assert (first.raw, clock()) == (b"084001", datetime(2026, 10, 23, 8, 40, 1, tzinfo=IST))
    clock.at = datetime(2026, 10, 23, 8, 40, 30, tzinfo=IST)
    second = part.answer(date(2026, 10, 23))
    assert (second.raw, clock()) == (b"084031", datetime(2026, 10, 23, 8, 40, 31, tzinfo=IST))
    with pytest.raises(PartFailed, match="rehearsal:NOT_RECORDED"):
        part.answer(date(2026, 10, 23))


def test_each_recorded_source_uses_its_one_rule():
    from pathlib import Path

    import fno.rehearsal as package

    def text(name):
        return (Path(package.__file__).parent / f"{name}.py").read_text()

    for name in ("recorded_candles", "recorded_closes"):
        assert "is_near(now, " in text(name)
    for name in ("recorded_cues", "recorded_preopen"):
        assert "ServedOnce()" in text(name) and "is_near" not in text(name)
    for name in ("recorded_cues", "recorded_candles", "recorded_preopen", "recorded_closes"):
        assert "timedelta(seconds=5)" not in text(name) and "NEAREST =" not in text(name)


def test_an_older_copy_is_never_served_after_a_newer_one():
    """The self-review's case: a read at 08:40:20 is served 08:40:31; the next, at 08:41:01, never gets 08:40:01."""
    early, late = datetime(2026, 10, 23, 8, 40, 1, tzinfo=IST), datetime(2026, 10, 23, 8, 40, 31, tzinfo=IST)
    served, copies = ServedOnce(), [(early, "early"), (late, "late")]
    assert served.pick(datetime(2026, 10, 23, 8, 40, 20, tzinfo=IST), copies) == (late, "late")
    assert served.pick(datetime(2026, 10, 23, 8, 41, 1, tzinfo=IST), copies) is None


def test_no_copy_at_all_is_none():
    assert ServedOnce().pick(READ, []) is None


def test_each_url_keeps_its_own_order(tmp_path):
    """Serving KOSPI's 08:50:34 copy never hides another index's copy saved earlier."""
    data, asx_url = b"{}", KOSPI_URL.replace("KS11", "AXJO")
    asx_path, asx_saved = "yahoo/preopen/2026/10/23/085030_asx200_5m.json", READ - 10 * SECOND
    sha = hashlib.sha256(data).hexdigest()
    rows = [
        f"{KOSPI_SAVED.isoformat()},{KOSPI_PATH},{KOSPI_URL},,{sha},2",
        f"{asx_saved.isoformat()},{asx_path},{asx_url},,{sha},2",
    ]
    (tmp_path / "cues.csv").write_text("fetched_at,path,url,form,sha256,size_bytes\n" + "\n".join(rows) + "\n")
    clock = Clock(READ)
    session = RecordedCueSession(tmp_path, {KOSPI_PATH: data, asx_path: data}.get, clock, clock.sleep)
    assert session.get(KOSPI_URL).content == data and session.get(asx_url).content == data
