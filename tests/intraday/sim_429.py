"""A simulated Groww mark for the 429-recovery tests (story A16-429-recovery): the real GW1a guard under the real A16
source, with no wall-clock timing in any result. Every pool thread keeps its own simulated time (set by the pacer's
slot for its call, moved by its own answer times), so thread scheduling cannot change a send time or a count. Real time
is used only to gate which thread checks the guard first, never to order simulated events."""

import threading
from datetime import datetime, timedelta

from fno.intraday.expiry_plan import ExpiryPlan
from fno.intraday.groww_source import PER_SECOND, WINDOW_ENDED, GrowwIntradaySource
from fno.intraday.read_only import ReadOnlyGroww
from fno.providers.groww_rate_guard import RateGuardedGroww, RateLimitPause
from tests.intraday.fakes import DAY, ist
from tests.intraday.groww_fakes import FakeGrowwApi, FakeGrowwProvider
from tests.intraday.test_groww_source import LISTED

MARK = ist(DAY, 10, 15)
QUOTES = 2 * 57 * 2  # both chains, 57 strikes, calls and puts (26-29 Oct's marks asked 216-224)
ANSWER_SECONDS = 0.8  # a 429 takes longer to come back than two pacer slots: the next calls are in flight
ANSWER_SPREAD_SECONDS = 0.5  # and the group's answers come back further apart than the resume margin


class Rate429(Exception):
    code = "429"


def _worker() -> bool:
    return threading.current_thread() is not threading.main_thread()


class SimClock:
    """`now()` is the thread's own simulated time on a pool thread, the latest time anyone reached on the main one."""

    def __init__(self, start: datetime):
        self.base = self.peak = start
        self.lock, self.local = threading.RLock(), threading.local()

    def now(self) -> datetime:
        return getattr(self.local, "t", self.base) if _worker() else self.peak

    def advance(self, seconds: float) -> None:
        with self.lock:
            if _worker():
                self.local.t = self.now() + timedelta(seconds=seconds)
                self.peak = max(self.peak, self.local.t)
            else:
                self.peak = self.base = self.peak + timedelta(seconds=seconds)

    sleep = advance


class SlotPacer:
    """4 a second in simulated time: slots in the order threads reach it. A pool thread's call gets its number here."""

    def __init__(self, clock: SimClock, gate=lambda number: None):
        self.clock, self.next, self.gate, self.count = clock, MARK, gate, 0

    def wait(self) -> None:
        clock, number = self.clock, None
        with clock.lock:
            start = max(clock.now(), self.next, clock.base)
            self.next = start + timedelta(seconds=1 / PER_SECOND)
            if _worker():
                self.count += 1
                clock.local.t, clock.local.number = start, self.count
                number = self.count
            clock.peak = max(clock.peak, start)
            if not _worker():
                clock.base = clock.peak
        if number:
            self.gate(number)


class TimedApi(FakeGrowwApi):
    """Answers 429 to the quote calls numbered `limited`. The first `in_flight` of them (and the call after them) are
    inside Groww together before any is answered, each answered ANSWER_SECONDS after its own slot."""

    def __init__(self, clock: SimClock, limited, chain_seconds: float = 0.0, in_flight: int = 1):
        super().__init__(index_level=24000.0)  # 6% band: 22600-25400, 57 strikes
        self.clock, self.limited, self.chain_seconds = clock, sorted(limited), chain_seconds
        self.group = self.limited[:in_flight]
        self.answered_429: list[tuple[str, datetime]] = []
        self.observed = lambda: True  # set by `mark_with`: has the source noted a 429 yet
        self._together = threading.Barrier(in_flight + 1, timeout=10) if in_flight > 1 else None
        self._group_answered = threading.Event()

    def gate(self, number: int) -> None:
        """Calls after the group wait, in real time, until it is answered: they then meet the guard's pause as they
        would have after the real answers."""
        if self.group and number > self.group[-1] + (1 if self._together else 0):
            self._group_answered.wait(10)

    def get_quote(self, trading_symbol, exchange, segment, timeout=None):
        number = getattr(self.clock.local, "number", None) if _worker() else None
        if number in self.limited:
            self._answer_429(trading_symbol, number)
        elif number and self._together and number == self.group[-1] + 1:
            self._together.wait()  # in flight beside the group, sent before its first answer
        return super().get_quote(trading_symbol, exchange, segment, timeout)

    def _answer_429(self, symbol: str, number: int) -> None:
        if self._together and number in self.group:
            self._together.wait()
            self.clock.advance(ANSWER_SECONDS + ANSWER_SPREAD_SECONDS * self.group.index(number))
            while number != self.group[0] and not self.observed():  # the source notes the first answer first
                self._group_answered.wait(0.001)
        with self.clock.lock:
            self.answered_429.append((symbol, self.clock.now()))
            if number in self.group and sum(1 for _ in self.answered_429) == len(self.group):
                self._group_answered.set()
        raise Rate429()

    def get_option_chain(self, exchange, underlying, expiry_date, timeout=None):
        self.clock.advance(self.chain_seconds)
        return super().get_option_chain(exchange, underlying, expiry_date, timeout)


def mark_with(limited, chain_seconds: float = 0.0, api: FakeGrowwApi | None = None, in_flight: int = 1):
    clock = SimClock(MARK)
    api = api or TimedApi(clock, limited, chain_seconds, in_flight)
    sleeps: list[float] = []

    def sleep(seconds: float) -> None:  # what the source waits for itself
        sleeps.append(seconds)
        clock.sleep(seconds)

    pause = RateLimitPause(clock=lambda: (clock.now() - MARK).total_seconds())
    guarded = RateGuardedGroww(lambda: FakeGrowwProvider(api).api, pause)
    source = GrowwIntradaySource(ReadOnlyGroww(lambda: guarded), ExpiryPlan(lambda: LISTED), 75, clock.now,
                                 SlotPacer(clock, getattr(api, "gate", lambda number: None)), sleep)  # fmt: skip
    if isinstance(api, TimedApi):
        api.observed = lambda: source._first_429 is not None
    doc = source.take(DAY, MARK)
    doc.sleeps, doc.api = sleeps, api
    return doc


def lost(doc) -> int:
    return sum(1 for q in doc.quotes if q.failure)


def asked_times(doc) -> list[datetime]:
    """When each call that reached Groww was sent (refused and unasked calls never did)."""
    calls = [doc.index, doc.future, *doc.chains, *doc.quotes]
    return sorted(c.request_sent_at for c in calls if c and c.failure not in ("GrowwRateLimitPaused", WINDOW_ENDED))
