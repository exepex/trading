"""Story GW1 (judges 637 SF1-SF2, 638 finding 2): Groww's 5 a second is never exceeded by any set of readers. A16 asks
at 4 a second and only inside its mark's quiet window, where every other reader is refused: a late or long mark asks
nothing after it. One A16 run at most takes a mark. The arithmetic below covers every set that can overlap."""

from datetime import datetime, timedelta

import pytest

from fno.intraday.candle_source import MIN_GAP_SECONDS
from fno.intraday.expiry_plan import ExpiryPlan
from fno.intraday.groww_source import PER_SECOND, WINDOW_ENDED, GrowwIntradaySource
from fno.intraday.read_only import ReadOnlyGroww
from fno.providers.groww_quiet_windows import QUIET_SECONDS
from fno.quotes.indices import INDEX_PER_SECOND
from tests.intraday.fakes import DAY, ist
from tests.intraday.groww_fakes import FakeGrowwApi, FakeGrowwProvider
from tests.intraday.test_groww_source import LISTED

GROWW_PER_SECOND = 5  # 300 a minute (research/school/probes/2026-10-22-p0-1-groww-chain.md)
# Unpaced sequential readers, measured: 54-71 contracts a minute on 15-23 Oct (12 sidecars); bounded by Groww's
# answer time, not by a pacer (judge 637 m3): 1.2 a second, kept as the measured ceiling.
UNPACED_MEASURED = 71 / 60


class CountingPacer:
    def __init__(self):
        self.waits = 0

    def wait(self):
        self.waits += 1


class TickingClock:
    """Moves `step` seconds on each reading, as a slow mark does."""

    def __init__(self, start: datetime, step: float):
        self.at, self.step = start, step

    def __call__(self):
        now = self.at
        self.at += timedelta(seconds=self.step)
        return now


def adapter(clock):
    api, pacer = FakeGrowwApi(), CountingPacer()
    provider = FakeGrowwProvider(api)
    source = GrowwIntradaySource(ReadOnlyGroww(lambda: provider.api), ExpiryPlan(lambda: LISTED), 75, clock, pacer)
    return source, pacer, api


def asked(doc):
    return [c for c in [doc.index, doc.future, *doc.chains, *doc.quotes] if c is not None and c.failure != WINDOW_ENDED]


def test_an_on_time_mark_asks_every_call_paced_inside_its_window():
    mark = ist(DAY, 10, 0)
    source, pacer, api = adapter(TickingClock(mark, 0.01))
    doc = source.take(DAY, mark)
    calls = [doc.index, doc.future, *doc.chains, *doc.quotes]
    assert not [c for c in calls if c.failure == WINDOW_ENDED] and pacer.waits == len(calls) == len(api.calls)


def test_a_slow_mark_asks_nothing_after_its_quiet_window_and_records_the_rest_unasked():
    """A slow Groww (each reading 1 s later): no request starts at or after mark + QUIET_SECONDS."""
    mark = ist(DAY, 10, 0)
    window_end = mark + timedelta(seconds=QUIET_SECONDS)
    source, _, api = adapter(TickingClock(mark, 1.0))
    doc = source.take(DAY, mark)
    unasked = [q for q in doc.quotes if q.failure == WINDOW_ENDED]
    assert unasked and all(c.request_sent_at < window_end for c in asked(doc))
    assert len(api.calls) == len(asked(doc))  # Groww saw only the asked calls


def test_a_late_mark_is_bounded_by_the_window_from_the_mark_not_from_its_start():
    """Judge 637 SF2: taken 110 s late (allowed to 120), it has 10 s; everything after is unasked."""
    mark = ist(DAY, 10, 0)
    source, _, api = adapter(TickingClock(mark + timedelta(seconds=110), 0.05))
    doc = source.take(DAY, mark)
    window_end = mark + timedelta(seconds=QUIET_SECONDS)
    assert doc.index.failure != WINDOW_ENDED  # the index still goes first, in time
    assert [q for q in doc.quotes if q.failure == WINDOW_ENDED]
    assert all(c.request_sent_at < window_end for c in asked(doc)) and len(api.calls) == len(asked(doc))


def test_a_mark_taken_after_its_window_asks_nothing():
    mark = ist(DAY, 10, 0)
    source, _, api = adapter(TickingClock(mark + timedelta(seconds=QUIET_SECONDS), 0.01))
    doc = source.take(DAY, mark)
    assert asked(doc) == [] and api.calls == [] and doc.index.failure == WINDOW_ENDED


# Every set of Groww readers that can run in the same second (CLAUDE.md's schedules; story GW1's table). A16 asks
# nothing outside its windows, so outside them each reader is alone.
OUTSIDE_A16_WINDOWS = {
    "the 3 pm NIFTY capture (14:55-15:10)": UNPACED_MEASURED,
    "A4c (15:02-15:13, after NIFTY ends)": INDEX_PER_SECOND,
    "the v4 capture (14:32-14:40)": UNPACED_MEASURED,
    "E3's execution capture (15:17-15:23)": UNPACED_MEASURED,
    "A16b's candles (15:33)": 1 / MIN_GAP_SECONDS,
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


# E3's captures 19-23 Oct (journal/execution/*.json and the 19 Oct sidecar): 2m57s at the longest (judge 638)
LONGEST_E3_CAPTURE = timedelta(minutes=2, seconds=57)
SNAPSHOT_COMMIT = timedelta(seconds=13)  # capture end to the snapshot step's end, 22-23 Oct run logs
TO_THE_SCHOOL = timedelta(seconds=80)  # the snapshot step's end to the school's start (fills ... premium_ranges)


def test_e3s_capture_ends_before_fills_by_with_a_pause_and_a_minute_to_spare():
    """Judge 638 finding 1 (the orchestrator's decision, 25 Oct): the capture now asks from execution_snapshot +
    QUIET_SECONDS; its longest recorded run plus one 60 s 429 pause plus 60 s must end by fills_by (C3's window end)."""
    from fno.config import load_config
    from fno.providers.groww_rate_guard import PAUSE_SECONDS

    times = load_config()["desk"]["timetable"]
    day = datetime(2026, 10, 26)
    snapshot, fills_by = (datetime.combine(day, datetime.strptime(times[k], "%H:%M").time())
                          for k in ("execution_snapshot", "fills_by"))  # fmt: skip
    capture_end = snapshot + timedelta(seconds=QUIET_SECONDS) + LONGEST_E3_CAPTURE + timedelta(seconds=PAUSE_SECONDS)
    assert capture_end + timedelta(seconds=60) <= fills_by


def test_the_school_still_starts_by_its_limit_after_that_capture():
    from fno.config import load_config
    from fno.daily.wiring import SCHOOL_STARTS_BY
    from fno.providers.groww_rate_guard import PAUSE_SECONDS

    snapshot = load_config()["desk"]["timetable"]["execution_snapshot"]
    start = datetime.combine(datetime(2026, 10, 26), datetime.strptime(snapshot, "%H:%M").time())
    first_call = start + timedelta(seconds=QUIET_SECONDS)
    school = first_call + LONGEST_E3_CAPTURE + timedelta(seconds=PAUSE_SECONDS) + SNAPSHOT_COMMIT + TO_THE_SCHOOL
    assert school.time() <= SCHOOL_STARTS_BY


class SleepingPacer:
    """A pacer whose wait takes a second of the clock, as a real one does when it holds a call back."""

    def __init__(self, clock):
        self.clock = clock

    def wait(self):
        self.clock.at += timedelta(seconds=1)


def test_a_calls_send_time_is_taken_after_its_pacer_wait():
    """Judge 638 addendum 1, plant J3: stamped before the wait, A16's send times would be early by the wait."""
    mark = ist(DAY, 10, 0)
    clock = TickingClock(mark, 0.0)
    provider = FakeGrowwProvider(FakeGrowwApi())
    source = GrowwIntradaySource(ReadOnlyGroww(lambda: provider.api), ExpiryPlan(lambda: LISTED), 75, clock,
                                 SleepingPacer(clock))  # fmt: skip
    doc = source.take(DAY, mark)
    assert doc.index.request_sent_at == mark + timedelta(seconds=1)  # the first call: one wait, then its stamp
