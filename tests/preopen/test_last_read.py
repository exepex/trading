"""A22e, criteria E1-E3 and judge 604's m1: the index parts' last read starts at 09:10:45 (15 s before the close),
every other part's still 1 s before; the real `GrowwIndexPreopen` over a candle source whose calls take time."""

from __future__ import annotations

from datetime import timedelta

from fno.intraday.candle_source import CandleAnswer, CandleCallFailed
from fno.preopen.parts import FO_WINDOW, GIFT_WINDOW, GrowwIndexPreopen
from fno.preopen.run import INCOMPLETE, LATE, OK, PreopenRun

from .fakes import FakeClock, ScriptedPart, complete, never
from .fixtures import DAY, candles, ist


class TimedCandles:
    """A Groww candle source whose n-th call takes `takes[n]` seconds and answers `answers[n]` (bytes or an error)."""

    def __init__(self, clock: FakeClock, answers: list, takes: float = 0.0):
        self.clock, self.answers, self.takes, self.requested = clock, answers, takes, []
        self.slow_from = None  # from this time on, each call takes 30 s (Groww's call timeout)

    def minute_candles(self, day):
        self.requested.append(self.clock.now())
        answer = self.answers[min(len(self.requested), len(self.answers)) - 1]
        slow = self.slow_from is not None and self.clock.now() >= self.slow_from
        self.clock.at += timedelta(seconds=30 if slow else self.takes)
        if isinstance(answer, Exception):
            raise answer
        return CandleAnswer("1m", day, day, answer, [], self.clock.now(), self.clock.now())


def _index(name: str, clock: FakeClock, answers: list, takes: float = 0.0) -> tuple[GrowwIndexPreopen, TimedCandles]:
    source = TimedCandles(clock, answers, takes)
    return GrowwIndexPreopen(name, source), source


def _run(clock, *parts):
    return {r.part: r for r in PreopenRun(parts, clock.now, clock.sleep).run(DAY)}


FAILED_CALL = CandleCallFailed("Groww 1m 2026-10-22..2026-10-22: Timeout")


def test_e1_the_index_parts_last_read_is_0910_45_and_the_others_keep_1_s():
    clock = FakeClock(ist(8, 36))
    gift, fo = ScriptedPart("gift", GIFT_WINDOW, clock, never()), ScriptedPart("fo_list", FO_WINDOW, clock, never())
    nifty, nifty_calls = _index("nifty", clock, [candles(count=9)])
    bank, bank_calls = _index("banknifty", clock, [candles(count=9)])
    results = _run(clock, gift, fo, nifty, bank)
    reads = [ist(9, 10), ist(9, 10, 30), ist(9, 10, 45)]  # never 09:10:59
    assert nifty_calls.requested == reads and bank_calls.requested == reads
    assert (results["nifty"].status, results["nifty"].reads) == (INCOMPLETE, 3)
    assert gift.read_at[-1] == ist(8, 44, 59) and fo.read_at[-1] == ist(9, 10, 59)


def test_e2_both_indices_complete_at_their_last_read_are_ok_with_2_s_calls():
    clock = FakeClock(ist(9, 10))
    nifty, _ = _index("nifty", clock, [FAILED_CALL, FAILED_CALL, candles()], takes=2)
    bank, bank_calls = _index("banknifty", clock, [FAILED_CALL, FAILED_CALL, candles()], takes=2)
    results = _run(clock, nifty, bank)
    assert (results["nifty"].status, results["banknifty"].status) == (OK, OK)
    assert bank_calls.requested[-1] == ist(9, 10, 47) and results["banknifty"].answer.seen_at == ist(9, 10, 49)


def test_e2_bad_case_with_the_old_1_s_margin_the_second_index_is_late():
    clock = FakeClock(ist(9, 10))
    nifty, _ = _index("nifty", clock, [FAILED_CALL, FAILED_CALL, candles()], takes=2)
    bank, _ = _index("banknifty", clock, [FAILED_CALL, FAILED_CALL, candles()], takes=2)
    nifty.last_read_margin = bank.last_read_margin = timedelta(seconds=1)  # A22d's plan
    results = _run(clock, nifty, bank)
    assert results["banknifty"].status == LATE and results["banknifty"].detail == "seen 09:11:03"


def test_e2_boundary_an_answer_received_at_0911_00_is_late_at_0910_59_ok():
    for takes, status in ((14, OK), (15, LATE), (16, LATE)):
        clock = FakeClock(ist(9, 10, 45))  # the last read itself, taking `takes` seconds
        part, _ = _index("nifty", clock, [candles()], takes=takes)
        [result] = PreopenRun([part], clock.now, clock.sleep).run(DAY)
        assert result.status == status, takes


def test_e3_a_part_without_its_own_margin_keeps_1_s_and_a_margin_past_the_window_reads_once_at_the_opening():
    clock = FakeClock(ist(9, 8))
    fo = ScriptedPart("fo_list", FO_WINDOW, clock, never())
    _run(clock, fo)
    assert fo.read_at[-1] == ist(9, 10, 59)
    clock = FakeClock(ist(9, 8))
    wide = ScriptedPart("fo_list", FO_WINDOW, clock, never())
    wide.last_read_margin = timedelta(minutes=5)
    result = _run(clock, wide)["fo_list"]
    assert wide.read_at == [ist(9, 8, 30)] and (result.status, result.reads) == (INCOMPLETE, 1)


def test_m1_slow_index_calls_at_0910_45_delay_the_fo_lists_last_read_which_is_then_late():
    """Judge 604 m1, stated in the rule: parts are read one at a time, so two 30 s index calls from 09:10:45 push the
    F&O list's 09:10:59 read to 09:11:45; complete then, it is `late` (seen after the close), never `ok`."""
    clock = FakeClock(ist(9, 8, 30))
    fo = ScriptedPart("fo_list", FO_WINDOW, clock, lambda n, now: complete()(n, now) if n >= 6 else never()(n, now))
    nifty, nifty_calls = _index("nifty", clock, [candles(count=9)])
    bank, bank_calls = _index("banknifty", clock, [candles(count=9)])
    for source in (nifty_calls, bank_calls):
        source.slow_from = ist(9, 10, 45)
    results = _run(clock, fo, nifty, bank)
    assert nifty_calls.requested[-1] == ist(9, 10, 45) and bank_calls.requested[-1] == ist(9, 11, 15)
    assert fo.read_at[-1] == ist(9, 11, 45) and len(fo.read_at) == 6
    assert results["fo_list"].status == LATE and results["fo_list"].detail == "seen 09:11:45"
