"""E8 rule 11 and acceptance 10: every Drive or A16 read is capped as a whole call, so a hung or trickling read fails
the step instead of holding up the day's exits (judge D, judge 178 addendum 5; judge 193 addenda 4 and 6)."""

from __future__ import annotations

import threading
import time

import pytest

from fno.desk.owner_timing.timed_reads import StepDeadline, StepTimedOut, TimedStore
from tests.desk.builders import DictStore


class HungStore(DictStore):
    """A read that never answers (released at the end of the test)."""

    def __init__(self):
        super().__init__()
        self.release = threading.Event()

    def get(self, path):
        self.release.wait()
        return b""


class TricklingStore(DictStore):
    """A server that sends a byte every 50 ms: no single wait is long, the whole read is."""

    def get(self, path):
        data = b""
        for _ in range(40):
            time.sleep(0.05)
            data += b"x"
        return data


def test_a_hung_read_times_out():
    store = HungStore()
    try:
        with pytest.raises(StepTimedOut, match="reading a/b"):
            TimedStore(store, StepDeadline(), cap_seconds=0.2).get("a/b")
    finally:
        store.release.set()


def test_a_trickling_read_is_capped_as_a_whole():
    started = time.monotonic()
    with pytest.raises(StepTimedOut):
        TimedStore(TricklingStore(), StepDeadline(), cap_seconds=0.5).get("a/b")
    assert time.monotonic() - started < 1.5  # the 2-second trickle was cut at its 0.5-second cap


def test_slow_reads_past_the_step_deadline_fail():
    now = [0.0]
    deadline = StepDeadline(limit_seconds=600, clock=lambda: now[0])
    store = DictStore()
    store.put("a", b"1")
    timed = TimedStore(store, deadline)
    assert timed.get("a") == b"1"
    now[0] = 601.0  # ten minutes of slow reads have passed
    with pytest.raises(StepTimedOut):
        timed.get("a")


def test_a_failed_read_keeps_its_error():
    class Broken(DictStore):
        def get(self, path):
            raise ConnectionError("drive down")

    with pytest.raises(ConnectionError):
        TimedStore(Broken(), StepDeadline()).get("a")
