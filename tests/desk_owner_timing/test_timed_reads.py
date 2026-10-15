"""E8 rule 11 and acceptance 10: every Drive or A16 read is capped as a whole call, so a hung or trickling read fails
the step instead of holding up the day's exits (judge D, judge 178 addendum 5; judge 193 addenda 4 and 6)."""

from __future__ import annotations

import threading
import time
from datetime import date

import pytest

from fno.desk.owner_timing.availability import AvailabilitySealer
from fno.desk.owner_timing.timed_reads import StepDeadline, StepTimedOut, TimedIndexStore, TimedStore
from fno.storage.index_store import IndexFileStore
from fno.storage.raw_store import ReadOnlyStoreError
from tests.desk.builders import DictStore
from tests.desk_owner_timing.fakes import MemorySeals, ist


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


def test_the_timed_store_never_writes():
    store = DictStore()
    with pytest.raises(ReadOnlyStoreError):
        TimedStore(store, StepDeadline()).put("a", b"1")
    assert store.get("a") is None


def test_no_write_starts_after_a_timed_out_read():
    """Judge 203 sf 2: a seal is written only after its read returned, so a hung read leaves no seal behind."""
    store, seals = HungStore(), MemorySeals()
    try:
        with pytest.raises(StepTimedOut):
            AvailabilitySealer(TimedStore(store, StepDeadline(), cap_seconds=0.2), "a", seals).seal(
                ist(date(2026, 10, 15), 14, 33)
            )
    finally:
        store.release.set()
    time.sleep(0.05)  # let the released read return: its result must still be ignored
    assert seals.latest() is None


class HungIndex(IndexFileStore):
    def __init__(self):
        self.release, self.written = threading.Event(), {}

    def get(self, path):
        self.release.wait()
        return None

    def replace(self, path, data):
        time.sleep(0.3)  # a slow push longer than the read cap
        self.written[path] = data


def test_e2cs_pulls_are_capped_and_its_pushes_made_in_full():
    store = HungIndex()
    timed = TimedIndexStore(store, StepDeadline(), cap_seconds=0.2)
    try:
        with pytest.raises(StepTimedOut):
            timed.get("book1_rules/ledger.csv")
    finally:
        store.release.set()
    timed.replace("book1_rules/ledger.csv", b"rows")
    assert store.written == {"book1_rules/ledger.csv": b"rows"}


def test_the_deadline_counts_from_the_steps_start():
    now = [0.0]
    deadline = StepDeadline(limit_seconds=600, clock=lambda: now[0])
    now[0] = 900.0  # the run was built long before the step ran
    deadline.restart()
    assert deadline.remaining() == 600
