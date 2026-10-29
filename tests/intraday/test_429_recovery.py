"""Story A16-429-recovery (orchestrator go, 29 Oct 2026): the real GW1a guard (60 s pause after a 429) under the real
A16 source on one simulated timeline. 29 Oct 10:15 lost 112 of 220 quotes to `GrowwRateLimitPaused`: the retry pass ran
inside the pause. Now it waits the pause out, asks nothing inside it, never asks after the mark's 120 s quiet window and
never faster than 4 a second, and the mark's notes keep the first 429 (the retry used to overwrite its call)."""

import threading
import time
from datetime import datetime, timedelta

import pytest

from fno.intraday.expiry_plan import ExpiryPlan
from fno.intraday.groww_source import FIRST_429, PER_SECOND, WINDOW_ENDED, GrowwIntradaySource
from fno.intraday.read_only import ReadOnlyGroww
from fno.providers.groww_quiet_windows import QUIET_SECONDS
from fno.providers.groww_rate_guard import PAUSE_SECONDS, RateGuardedGroww, RateLimitPause
from tests.intraday.fakes import DAY, FakeClock, ist
from tests.intraday.groww_fakes import FakeGrowwApi, FakeGrowwProvider
from tests.intraday.test_groww_source import LISTED

MARK = ist(DAY, 10, 15)
QUOTES = 2 * 57 * 2  # both chains, 57 strikes, calls and puts (26-29 Oct's marks asked 216-224)


class Rate429(Exception):
    code = "429"


class TimedApi(FakeGrowwApi):
    """Takes `latency` seconds a call on the shared clock; answers 429 on the quote calls numbered `limited`."""

    def __init__(self, clock: FakeClock, limited: range, chain_seconds: float = 0.0, in_flight: int = 0):
        super().__init__(index_level=24000.0)  # 6% band: 22600-25400, 57 strikes
        self.clock, self.limited, self.chain_seconds = clock, limited, chain_seconds
        self.sent_at: list[datetime] = []
        self.quote_calls = 0
        self.answered_429: list[tuple[str, datetime]] = []  # in the order Groww answered
        self._together = threading.Barrier(in_flight, timeout=5) if in_flight > 1 else None
        self._released, self._all_answered = threading.Event(), threading.Event()

    def get_quote(self, trading_symbol, exchange, segment, timeout=None):
        self.sent_at.append(self.clock.now())
        if segment == self.SEGMENT_FNO and trading_symbol.startswith("NIFTY26") and "FUT" not in trading_symbol:
            with self.clock.lock:
                self.quote_calls += 1
                number = self.quote_calls
            if number in self.limited:
                self._answer_429(trading_symbol, number - self.limited.start)
            elif self._together and number >= self.limited.stop:
                self._all_answered.wait(5)  # in flight with them: sent now, answered once they have been
        return super().get_quote(trading_symbol, exchange, segment, timeout)

    def _answer_429(self, symbol: str, order: int) -> None:
        """Calls in flight together all meet Groww's limit, 0.3 s of the shared clock apart, in `order`."""
        if self._together:
            self._together.wait()
            self._released.set()
            time.sleep(0.15 * order)  # real time: fixes who is answered first
        with self.clock.lock:
            self.clock.advance(0.3)
            self.answered_429.append((symbol, self.clock.now()))
            if len(self.answered_429) == len(self.limited):
                self._all_answered.set()
        raise Rate429()

    def hold(self) -> None:
        """Groww's answers take real time: the clock of the next calls waits for them (else it races ahead)."""
        if self._released.is_set():
            self._all_answered.wait(5)

    def get_option_chain(self, exchange, underlying, expiry_date, timeout=None):
        self.sent_at.append(self.clock.now())
        self.clock.advance(self.chain_seconds)
        return super().get_option_chain(exchange, underlying, expiry_date, timeout)


class QuarterSecondPacer:
    """4 a second on the shared clock: each call starts 0.25 s after the previous one."""

    def __init__(self, clock: FakeClock, hold=lambda: None):
        self.clock, self.next, self.lock, self.hold = clock, MARK, clock.lock, hold

    def wait(self) -> None:
        self.hold()
        with self.lock:
            start = max(self.clock.now(), self.next)
            self.next = start + timedelta(seconds=1 / PER_SECOND)
            self.clock.moment = max(self.clock.moment, start)  # the clock never runs backwards


def mark_with(limited: range, chain_seconds: float = 0.0, api: FakeGrowwApi | None = None, in_flight: int = 0):
    clock = FakeClock(MARK)
    clock.lock = threading.RLock()  # the pacer and the answers move one clock
    api = api or TimedApi(clock, limited, chain_seconds, in_flight)
    sleeps: list[float] = []

    def sleep(seconds: float) -> None:  # what the source waits for itself (the pacer moves the clock on its own)
        sleeps.append(seconds)
        clock.sleep(seconds)

    pause = RateLimitPause(clock=lambda: (clock.now() - MARK).total_seconds())
    guarded = RateGuardedGroww(lambda: FakeGrowwProvider(api).api, pause)
    source = GrowwIntradaySource(ReadOnlyGroww(lambda: guarded), ExpiryPlan(lambda: LISTED), 75, clock.now,
                                 QuarterSecondPacer(clock, getattr(api, 'hold', lambda: None)), sleep)  # fmt: skip
    doc = source.take(DAY, MARK)
    doc.sleeps, doc.api = sleeps, api
    return doc


def lost(doc) -> int:
    return sum(1 for q in doc.quotes if q.failure)


def answered_429(doc) -> datetime:
    note = next(n for n in doc.notes if n.startswith("first_429"))
    return datetime.fromisoformat(note.split(" answered ")[1].split()[0])


def window_end() -> datetime:
    return MARK + timedelta(seconds=QUIET_SECONDS)


def test_a_429_after_91_quotes_loses_nothing_now_where_29_oct_lost_112_of_220():
    doc = mark_with(range(92, 93))  # 29 Oct 10:15: about 130 quotes were refused in the first pass
    assert len(doc.quotes) == QUOTES and any(n.startswith("quotes_retried:") for n in doc.notes)
    assert lost(doc) == 0 and doc.recorded_contracts == doc.expected_contracts
    assert doc.sleeps and sum(doc.sleeps) <= PAUSE_SECONDS  # it waited out the pause, once, and no longer


def test_the_retry_asks_nothing_inside_the_pause_and_nothing_after_the_quiet_window():
    doc = mark_with(range(30, 31), chain_seconds=2.5)
    answered = answered_429(doc)
    assert [t for t in doc.api.sent_at if answered < t < answered + timedelta(seconds=PAUSE_SECONDS)] == []
    assert max(doc.api.sent_at) < window_end()
    assert not any(q.failure == "GrowwRateLimitPaused" for q in doc.quotes)


def test_a_429_on_the_first_quote_recovers_all_that_fits_and_names_the_rest_unasked():
    """Worst case: 5 s of chain calls, a 429 on the first quote, the pause ends about 66 s in, and 228 quotes at 4 a
    second need 57 s more: the last quotes that cannot start before 120 s stay unasked and named."""
    doc = mark_with(range(1, 2), chain_seconds=2.5)
    resume = answered_429(doc) + timedelta(seconds=PAUSE_SECONDS)
    fits = int((window_end() - resume).total_seconds() * PER_SECOND)
    assert abs(lost(doc) - max(0, QUOTES - fits)) <= 2
    assert {q.failure for q in doc.quotes if q.failure} <= {WINDOW_ENDED}
    assert max(doc.api.sent_at) < window_end()


def test_the_retry_never_goes_faster_than_4_a_second():
    doc = mark_with(range(30, 31))
    times = sorted(doc.api.sent_at)
    assert min((b - a).total_seconds() for a, b in zip(times, times[1:], strict=False)) >= 1 / PER_SECOND - 1e-6


def test_the_first_429_stays_in_the_notes_with_its_call_time_and_code():
    doc = mark_with(range(10, 12))
    notes = [n for n in doc.notes if n.startswith("first_429")]
    assert len(notes) == 1 and "quote NIFTY26" in notes[0] and notes[0].endswith("GrowwRateLimited:429")
    assert notes[0].startswith(FIRST_429.split("{")[0])


def test_a_late_429_whose_pause_outlasts_the_window_skips_the_retry_and_says_so():
    doc = mark_with(range(226, 227), chain_seconds=2.5)  # 61 s in: the pause would end at 121.5 s
    assert any(n.startswith("quotes_retry_skipped") for n in doc.notes)
    assert not any(n.startswith("quotes_retried") for n in doc.notes) and not doc.sleeps
    assert max(doc.api.sent_at) < window_end()


def test_a_mark_without_a_429_is_unchanged():
    doc = mark_with(range(0))
    assert lost(doc) == 0 and not doc.sleeps and not any("429" in n or "retr" in n for n in doc.notes)


def test_a_failure_that_is_not_a_429_is_retried_at_once_without_waiting():
    doc = mark_with(range(0), api=FakeGrowwApi(index_level=24000.0, fail=("NIFTY26101922600CE",)))
    assert "quotes_retried:1" in doc.notes and not doc.sleeps
    assert not any(n.startswith("first_429") for n in doc.notes)


@pytest.mark.parametrize("limited", [range(5, 6), range(50, 51), range(150, 151), range(1, 2)])
def test_the_real_29_oct_shapes_all_end_inside_the_window(limited):
    doc = mark_with(limited, chain_seconds=2.0)
    assert max(doc.api.sent_at) < window_end()


def test_429s_of_calls_in_flight_together_name_the_first_and_wait_for_the_last_pause():
    """4 workers: calls sent before the first 429 returns meet the limit too, and each restarts the guard's pause. The
    note names the first answered; the retry starts after the last pause, never inside an earlier one."""
    doc = mark_with(range(40, 43), chain_seconds=2.0, in_flight=3)
    (first, first_at), (_, _), (_, last_at) = doc.api.answered_429
    assert last_at - first_at >= timedelta(seconds=0.5)
    notes = [n for n in doc.notes if n.startswith("first_429")]
    assert len(notes) == 1 and f"quote {first}" in notes[0]  # the first answered, not the last
    assert abs((answered_429(doc) - first_at).total_seconds()) < 0.05
    last_pause_ends = last_at + timedelta(seconds=PAUSE_SECONDS)
    assert [t for t in doc.api.sent_at if first_at < t < last_pause_ends] == []  # nothing inside either pause
    assert not any(q.failure == "GrowwRateLimitPaused" for q in doc.quotes)  # so the retry was not refused
    retried = int(next(n for n in doc.notes if n.startswith("quotes_retried")).split(":")[1])
    fits = int((window_end() - last_pause_ends).total_seconds() * PER_SECOND)
    assert abs(lost(doc) - max(0, retried - fits)) <= 3  # what the window allows after the LAST pause, no more
    assert max(doc.api.sent_at) < window_end()
