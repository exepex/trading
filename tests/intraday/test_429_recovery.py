"""Story A16-429-recovery (orchestrator go, 29 Oct 2026): the real GW1a guard (60 s pause after a 429) under the real
A16 source on one simulated timeline. 29 Oct 10:15 lost 112 of 220 quotes to `GrowwRateLimitPaused`: the retry pass ran
inside the pause. Now it waits the pause out, asks nothing inside it, never asks after the mark's 120 s quiet window and
never faster than 4 a second, and the mark's notes keep the first 429 (the retry used to overwrite its call)."""

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

    def __init__(self, clock: FakeClock, limited: range, chain_seconds: float = 0.0):
        super().__init__(index_level=24000.0)  # 6% band: 22600-25400, 57 strikes
        self.clock, self.limited, self.chain_seconds = clock, limited, chain_seconds
        self.sent_at: list[datetime] = []
        self.quote_calls = 0

    def get_quote(self, trading_symbol, exchange, segment, timeout=None):
        self.sent_at.append(self.clock.now())
        if segment == self.SEGMENT_FNO and trading_symbol.startswith("NIFTY26") and "FUT" not in trading_symbol:
            self.quote_calls += 1
            if self.quote_calls in self.limited:
                raise Rate429()
        return super().get_quote(trading_symbol, exchange, segment, timeout)

    def get_option_chain(self, exchange, underlying, expiry_date, timeout=None):
        self.sent_at.append(self.clock.now())
        self.clock.advance(self.chain_seconds)
        return super().get_option_chain(exchange, underlying, expiry_date, timeout)


class QuarterSecondPacer:
    """4 a second on the shared clock: each call starts 0.25 s after the previous one."""

    def __init__(self, clock: FakeClock):
        self.clock, self.next = clock, MARK

    def wait(self) -> None:
        start = max(self.clock.now(), self.next)
        self.next = start + timedelta(seconds=1 / PER_SECOND)
        self.clock.moment = start


def mark_with(limited: range, chain_seconds: float = 0.0, api: FakeGrowwApi | None = None):
    clock = FakeClock(MARK)
    api = api or TimedApi(clock, limited, chain_seconds)
    sleeps: list[float] = []

    def sleep(seconds: float) -> None:  # what the source waits for itself (the pacer moves the clock on its own)
        sleeps.append(seconds)
        clock.sleep(seconds)

    pause = RateLimitPause(clock=lambda: (clock.now() - MARK).total_seconds())
    guarded = RateGuardedGroww(lambda: FakeGrowwProvider(api).api, pause)
    source = GrowwIntradaySource(ReadOnlyGroww(lambda: guarded), ExpiryPlan(lambda: LISTED), 75, clock.now,
                                 QuarterSecondPacer(clock), sleep)  # fmt: skip
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
