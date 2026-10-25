"""Story GW1 (judge 637 SF1, SF2): Groww's 5 a second is never exceeded by any set of readers. A16 asks at 4 a
second only inside its mark's quiet window, where every other reader is refused, and at 1 a second after it (a late
mark, a long one); one A16 run at most takes a mark. The arithmetic below covers every set that can overlap."""

from datetime import datetime, timedelta

import pytest

from fno.intraday.candle_source import MIN_GAP_SECONDS
from fno.intraday.expiry_plan import ExpiryPlan
from fno.intraday.groww_source import AFTER_WINDOW_PER_SECOND, FAST_LEAD, PER_SECOND, GrowwIntradaySource
from fno.intraday.read_only import ReadOnlyGroww
from fno.providers.groww_quiet_windows import QUIET_SECONDS
from fno.quotes.indices import INDEX_PER_SECOND
from tests.intraday.fakes import DAY, ist
from tests.intraday.groww_fakes import FakeGrowwProvider
from tests.intraday.test_groww_source import LISTED

GROWW_PER_SECOND = 5  # 300 a minute (research/school/probes/2026-10-22-p0-1-groww-chain.md)
# Unpaced sequential readers, measured: 54-71 contracts a minute on 15-23 Oct (12 sidecars); bounded by Groww's
# answer time, not by a pacer (judge 637 m3): 1.2 a second, kept as the measured ceiling.
UNPACED_MEASURED = 71 / 60


class CountingPacer:
    def __init__(self, clock=None):
        self.waits, self.clock, self.at = 0, clock, []

    def wait(self):
        self.waits += 1
        if self.clock is not None:
            self.at.append(self.clock.last)  # the reading that chose this pacer


class TickingClock:
    """Moves `step` seconds on each reading, as a slow mark does."""

    def __init__(self, start: datetime, step: float):
        self.at, self.step = start, step

    def __call__(self):
        now = self.last = self.at
        self.at += timedelta(seconds=self.step)
        return now


def adapter(clock):
    fast, slow = CountingPacer(clock), CountingPacer(clock)
    source = GrowwIntradaySource(ReadOnlyGroww(lambda: FakeGrowwProvider().api), ExpiryPlan(lambda: LISTED), 75,
                                 clock, fast, slow)  # fmt: skip
    return source, fast, slow


def test_an_on_time_mark_asks_at_the_fast_pace_inside_its_window():
    mark = ist(DAY, 10, 0)
    source, fast, slow = adapter(TickingClock(mark, 0.01))
    source.take(DAY, mark)
    assert fast.waits > 0 and slow.waits == 0


def test_a_mark_taken_after_its_quiet_window_asks_at_one_a_second_only():
    mark = ist(DAY, 10, 0)
    late = mark + timedelta(seconds=QUIET_SECONDS + 1)  # boundary + 1 s: a late start (allowed to mark + 120 s)
    source, fast, slow = adapter(TickingClock(late, 0.01))
    source.take(DAY, mark)
    assert fast.waits == 0 and slow.waits > 0


def test_a_long_mark_slows_down_before_its_window_ends():
    """No fast start can be booked past the window's end: the fast pace stops FAST_LEAD before it."""
    mark = ist(DAY, 10, 0)
    source, fast, slow = adapter(TickingClock(mark + timedelta(seconds=QUIET_SECONDS - 8), 0.05))
    source.take(DAY, mark)
    window_end = mark + timedelta(seconds=QUIET_SECONDS)
    assert fast.waits > 0 and slow.waits > 0
    assert max(fast.at) < window_end - FAST_LEAD <= min(slow.at)


def test_every_call_of_a_mark_is_paced_the_index_first():
    mark = ist(DAY, 10, 0)
    source, fast, slow = adapter(TickingClock(mark, 0.01))
    doc = source.take(DAY, mark)
    calls = 1 + 1 + len(doc.chains) + len(doc.quotes) + (doc.index_candle is not None)  # index, future, chains
    assert fast.waits == calls and slow.waits == 0


# Every set of Groww readers that can run in the same second (CLAUDE.md's schedules; story GW1's table).
OUTSIDE_A16_WINDOWS = {
    "A16 (late or long mark) + the 3 pm NIFTY capture (14:55-15:10)": AFTER_WINDOW_PER_SECOND + UNPACED_MEASURED,
    "A16 + A4c (15:02-15:13, after NIFTY ends)": AFTER_WINDOW_PER_SECOND + INDEX_PER_SECOND,
    "A16 + the v4 capture (14:32-14:40)": AFTER_WINDOW_PER_SECOND + UNPACED_MEASURED,
    "A16 + E3's execution capture (15:17-15:20)": AFTER_WINDOW_PER_SECOND + UNPACED_MEASURED,
    "A16 + A16b's candles (15:33)": AFTER_WINDOW_PER_SECOND + 1 / MIN_GAP_SECONDS,
}
INSIDE_A16_WINDOWS = {"A16 alone (one taker a mark; every get_provider reader refused)": PER_SECOND}


@pytest.mark.parametrize("readers", [*OUTSIDE_A16_WINDOWS, *INSIDE_A16_WINDOWS])
def test_no_set_of_readers_that_can_overlap_exceeds_five_a_second(readers):
    rate = {**OUTSIDE_A16_WINDOWS, **INSIDE_A16_WINDOWS}[readers]
    assert rate <= GROWW_PER_SECOND, f"{readers}: {rate:.2f} a second"


def test_the_orderings_the_table_relies_on_hold_in_the_code():
    """The table above counts only readers that can meet: these orderings keep the others apart."""
    from fno.config import load_config
    from fno.daily.quote_parts import QUOTE_PARTS
    from fno.quotes.indices import INDEX_WINDOW_END
    from fno.quotes.recorder import WINDOW_END, WINDOW_START

    parts = {part.name: part for part in QUOTE_PARTS}
    assert parts["indices"].starts_after == "nifty"  # A4c never beside the 3 pm NIFTY capture
    cfg = load_config()
    v4_end = datetime.strptime(cfg["quotes"]["windows"]["v4"]["end"], "%H:%M").time()
    assert v4_end < WINDOW_START  # v4 (to 14:40) never beside NIFTY (from 14:55)
    e3 = datetime.combine(DAY, datetime.strptime(cfg["desk"]["timetable"]["execution_snapshot"], "%H:%M").time())
    first_e3_call = (e3 + timedelta(seconds=QUIET_SECONDS)).time()
    assert first_e3_call > INDEX_WINDOW_END and first_e3_call > WINDOW_END  # E3 asks after A4c and NIFTY end
