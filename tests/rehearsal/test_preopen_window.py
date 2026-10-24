"""REH1l: a pre-open read is never served a copy seen at or after its window's close (L1), the 23 Oct record replayed
part by part (L2), and the rehearsal's own clock is never a capture's warning (L3)."""

import hashlib
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from fno.models import IST
from fno.preopen.parts import FO_WINDOW, GIFT_WINDOW, INDEX_WINDOW, PartFailed
from fno.rehearsal.recorded_preopen import RecordedPreopenPart
from fno.storage.receipts import Receipt, ReceiptFolder

D22, D23 = date(2026, 10, 22), date(2026, 10, 23)
RECORD = ReceiptFolder(Path(__file__).resolve().parents[2] / "receipts")  # the real record's receipts


def at(hhmmss: str, day=D23) -> datetime:
    return datetime(day.year, day.month, day.day, int(hhmmss[:2]), int(hhmmss[2:4]), int(hhmmss[4:6]), tzinfo=IST)


class Clock:
    def __init__(self, now):
        self.at = now

    def __call__(self):
        return self.at

    def sleep(self, seconds):
        self.at += timedelta(seconds=seconds)


class Part:
    last_read_margin = timedelta(seconds=15)

    def __init__(self, name, window):
        self.name, self.window = name, window

    def read(self, data, day, seen_at):
        return data


def part_over(tmp_path, name, window, stamps, now):
    """A part over a record holding one copy per `stamps` (HHMMSS), its bytes the stamp itself."""
    receipts, files = ReceiptFolder(tmp_path), {}
    for stamp in stamps:
        path = f"data/preopen/raw/2026/10/23/{name}_{stamp}.json"
        receipts.write(Receipt(path, hashlib.sha256(stamp.encode()).hexdigest(), 6, "2026-10-23T03:41:00+00:00",
                               "preopen record", "r"))  # fmt: skip
        files[path] = stamp.encode()
    clock = Clock(at(now))
    return RecordedPreopenPart(Part(name, window), receipts, files.get, clock, clock.sleep), clock


# L1: never past the window


def test_a_read_inside_the_window_is_never_served_a_copy_seen_after_its_close(tmp_path):
    part, clock = part_over(tmp_path, "banknifty", INDEX_WINDOW, ["091101"], "091000")
    with pytest.raises(PartFailed, match="rehearsal:NOT_RECORDED banknifty"):
        part.answer(D23)
    assert clock() == at("091000")  # no wait for a copy it may not have


@pytest.mark.parametrize(("stamp", "served"), [("091059", True), ("091100", False)])
def test_the_close_itself_is_outside_the_window(tmp_path, stamp, served):
    part, clock = part_over(tmp_path, "nifty", INDEX_WINDOW, [stamp], "091030")
    if served:
        assert part.answer(D23).raw == b"091059" and clock() == at("091059")  # waited for its seen time
    else:
        with pytest.raises(PartFailed, match="rehearsal:NOT_RECORDED"):
            part.answer(D23)


def test_a_late_copy_never_hides_an_earlier_one_inside_the_window(tmp_path):
    """Judge 616's condition: copies seen at or after the close are dropped before the choice, so a read at 09:10:45
    still gets the unserved 09:10:30 copy (nearer would be 09:11:01, 16 s ahead) and the next read cannot go back."""
    part, clock = part_over(tmp_path, "banknifty", INDEX_WINDOW, ["091030", "091101"], "091045")
    assert part.answer(D23).raw == b"091030" and clock() == at("091045")  # a copy before now: no wait
    with pytest.raises(PartFailed, match="rehearsal:NOT_RECORDED"):
        part.answer(D23)  # 09:11:01 is never served, and 09:10:30 never twice


# L2: the 23 Oct record, part by part, at the reads of A22e's plan


def nearest(name, window, now):
    part = RecordedPreopenPart(Part(name, window), RECORD, lambda path: None, lambda: now, None)
    found = part._nearest(now.date(), now)
    return found and found[0].rsplit("/", 1)[-1]


def test_the_23_oct_record_serves_gift_the_list_and_nifty_and_never_banknifty():
    assert nearest("gift", GIFT_WINDOW, at("084000")) == "gift_084000.json"
    assert nearest("fo_list", FO_WINDOW, at("090830")) == "fo_list_090830.json"
    assert nearest("nifty", INDEX_WINDOW, at("091000")) == "nifty_091059.json"  # inside its window: waited for
    assert [nearest("banknifty", INDEX_WINDOW, at(t)) for t in ("091000", "091030", "091045")] == [None] * 3


def test_22_oct_has_no_recorded_part_at_all():
    for name, window, first in (("gift", GIFT_WINDOW, "084000"), ("fo_list", FO_WINDOW, "090830"),
                                ("nifty", INDEX_WINDOW, "091000"), ("banknifty", INDEX_WINDOW, "091000")):  # fmt: skip
        assert nearest(name, window, at(first, D22)) is None


# L3: the rehearsal's clock is not a capture's warning; a real run's still is


def test_a_rehearsal_s_clock_check_gives_no_warning_and_a_real_one_still_does(monkeypatch, tmp_path):
    from fno.constants import ENV_FNO_REHEARSAL
    from fno.intraday.clock import CLOCK_UNCHECKED, ClockReading
    from fno.intraday.clock_wiring import build_clock_check
    from fno.rehearsal.mode import Rehearsal
    from fno.server_clock import SkewCheck

    monkeypatch.setenv(ENV_FNO_REHEARSAL, Rehearsal.new(D23, tmp_path, tmp_path).to_env())
    assert build_clock_check().check().warning() == ""  # so `preopen record` adds no clock problem
    unanswered = SkewCheck("github", None, False, "github: not checked")
    assert ClockReading(CLOCK_UNCHECKED, (unanswered,)).warning() == "github: not checked"  # the real day's rule
