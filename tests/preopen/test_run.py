"""Criterion 4: windows and retries at their exact boundaries, on an injected clock."""

from __future__ import annotations

from datetime import time

from fno.preopen.answers import Reading
from fno.preopen.parts import FO_WINDOW, GIFT_WINDOW, INDEX_WINDOW
from fno.preopen.run import FAILED, INCOMPLETE, LATE, OK, PreopenRun

from .fakes import FakeClock, ScriptedPart, complete, failing, never
from .fixtures import DAY, ist


def _run(clock, *parts, finished=None):
    return PreopenRun(parts, clock.now, clock.sleep, finished or (lambda result: None)).run(DAY)


def test_gift_waits_at_083959_and_reads_at_084000():
    clock = FakeClock(ist(8, 39, 59))
    part = ScriptedPart("gift", GIFT_WINDOW, clock, complete())
    [result] = _run(clock, part)
    assert part.read_at == [ist(8, 40)] and result.status == OK and result.reads == 1


def test_gift_at_084459_is_in_the_window_and_at_084500_late():
    for start, status in ((ist(8, 44, 59), OK), (ist(8, 45), LATE)):
        clock = FakeClock(start)
        [result] = _run(clock, ScriptedPart("gift", GIFT_WINDOW, clock, complete()))
        assert result.status == status and result.reads == 1


def test_preopen_reads_every_30_s_from_090830_to_091059_then_reports_incomplete():
    clock = FakeClock(ist(9, 0))
    part = ScriptedPart("fo_list", FO_WINDOW, clock, never("not final"))
    [result] = _run(clock, part)
    expected = [ist(9, 8, 30), ist(9, 9), ist(9, 9, 30), ist(9, 10), ist(9, 10, 30), ist(9, 10, 59)]
    assert part.read_at == expected and result.status == INCOMPLETE and result.detail == "not final"


def test_index_parts_read_at_091000_091030_091059():
    clock = FakeClock(ist(9, 0))
    part = ScriptedPart("nifty", INDEX_WINDOW, clock, never())
    _run(clock, part)
    assert part.read_at == [ist(9, 10), ist(9, 10, 30), ist(9, 10, 59)]


def test_stale_at_the_first_read_and_fresh_at_a_retry_is_ok():
    def stale_once(n, now):
        return Reading(n >= 2, now, {}, "" if n >= 2 else "stale")

    clock = FakeClock(ist(8, 40))
    [result] = _run(clock, ScriptedPart("gift", GIFT_WINDOW, clock, stale_once))
    assert result.status == OK and result.reads == 2 and result.detail == ""


def test_every_read_failing_is_failed_with_the_last_reason():
    clock = FakeClock(ist(8, 40))
    [result] = _run(clock, ScriptedPart("gift", GIFT_WINDOW, clock, failing))
    assert result.status == FAILED and result.answer is None and result.detail == "NSE: HTTP 503"


def test_a_failure_after_an_incomplete_answer_keeps_that_answer_as_incomplete():
    def incomplete_then_failing(n, now):
        return never("no 09:09 candle yet")(n, now) if n == 1 else failing(n, now)

    clock = FakeClock(ist(9, 10))
    [result] = _run(clock, ScriptedPart("nifty", INDEX_WINDOW, clock, incomplete_then_failing))
    assert result.status == INCOMPLETE and result.answer is not None and result.detail == "NSE: HTTP 503"


def test_a_read_seen_after_the_close_is_late_even_when_it_started_inside():
    clock = FakeClock(ist(8, 44, 59))
    [result] = _run(clock, ScriptedPart("gift", GIFT_WINDOW, clock, complete(), takes=2))
    assert result.status == LATE and "08:45:01" in result.detail


def test_overlapping_windows_read_in_time_order_and_each_is_handed_over_when_it_ends():
    clock = FakeClock(ist(8, 36))
    finished = []
    gift = ScriptedPart("gift", GIFT_WINDOW, clock, complete())
    fo = ScriptedPart("fo_list", FO_WINDOW, clock, lambda n, now: Reading(n >= 4, now, {}, ""))
    nifty = ScriptedPart("nifty", INDEX_WINDOW, clock, complete())
    results = _run(clock, gift, fo, nifty, finished=lambda r: finished.append((r.part, clock.now().time())))
    assert [r.status for r in results] == [OK, OK, OK]
    assert finished == [("gift", time(8, 40)), ("fo_list", time(9, 10)), ("nifty", time(9, 10))]
