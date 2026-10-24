"""Story O1-day-lock: one `daily run` per day per container, and every wait of a minute or more says so. On 23 Oct a
routine took A4h's 7-minute wait for a hang and started a second run beside the living one; both uploaded the same
close file to Drive."""

import subprocess
import sys
from argparse import Namespace
from datetime import date, datetime, timedelta

import pytest

from fno.daily.cli import cmd_daily_run
from fno.daily.day_lock import ALREADY_RUNNING, DayLock
from fno.daily.part_locks import PART_LOCKS
from fno.daily.wait_notice import WAITING, AnnouncedWaiter
from fno.desk.daily_ports import Waiter
from fno.models import IST

DAY = date(2026, 10, 23)
AT = datetime(2026, 10, 23, 14, 5, 12, tzinfo=IST)


def test_a_second_lock_of_the_same_day_is_refused_and_names_the_living_run_s_start(tmp_path):
    lock = DayLock(tmp_path)
    with lock.taken(DAY, AT) as first, lock.taken(DAY, AT + timedelta(minutes=95)) as second:
        assert first is None and second == "2026-10-23T14:05:12+05:30"
    with lock.taken(DAY, AT) as again:
        assert again is None  # freed when its holder ended, as a crashed or killed run's is
    with lock.taken(date(2026, 10, 26), AT) as other_day, lock.taken(DAY, AT) as same_again:
        assert other_day is None and same_again is None  # one lock per day


def test_a_child_started_by_the_run_never_keeps_the_day_s_lock(tmp_path):
    """The 3 pm parts outlive a crashed run on purpose (F1); the day's lock must not live on in them."""
    lock = DayLock(tmp_path)
    with lock.taken(DAY, AT):
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        with lock.taken(DAY, AT) as rerun:
            assert rerun is None and child.poll() is None  # the child lives on, the lock is free
    finally:
        child.kill()
        child.wait()


def test_a_lock_held_by_another_process_refuses_the_command_before_anything_is_built(tmp_path, monkeypatch):
    holder = subprocess.Popen([sys.executable, "-c", HOLDER, str(tmp_path / PART_LOCKS / f"{DAY}_run.lock")],
                              stdout=subprocess.PIPE, text=True)  # fmt: skip
    try:
        assert holder.stdout.readline().strip() == "held"

        def never(*args, **kwargs):
            raise AssertionError("a second run built its runner")

        monkeypatch.setattr("fno.daily.wiring.build_day_runner", never)
        printed = []
        assert cmd_daily_run(Namespace(day=DAY), printed.append, root=tmp_path) == 1
        assert printed == [ALREADY_RUNNING.format(day=DAY, since="2026-10-23T15:33:23+05:30")]
        assert not (tmp_path / "journal/runs" / f"{DAY}.json").exists()
    finally:
        holder.kill()
        holder.wait()


HOLDER = """import fcntl, os, sys, time
os.makedirs(os.path.dirname(sys.argv[1]), exist_ok=True)
fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT)
fcntl.flock(fd, fcntl.LOCK_EX)
os.write(fd, b"2026-10-23T15:33:23+05:30")
print("held", flush=True)
time.sleep(60)
"""


class Clock:
    def __init__(self):
        self.now = datetime(2026, 10, 23, 15, 33, tzinfo=IST)

    def __call__(self):
        return self.now


class Sleeper(Waiter):
    def __init__(self, clock):
        self.clock, self.waits = clock, []

    def until(self, moment):
        self.waits.append(moment)
        self.clock.now = max(self.clock.now, moment)


@pytest.fixture
def announced():
    clock, said = Clock(), []
    inner = Sleeper(clock)
    return AnnouncedWaiter(inner, clock, said.append), clock, inner, said


def test_a_wait_of_a_minute_or_more_says_until_when_before_it_starts(announced):
    waiter, clock, inner, said = announced
    moment = datetime(2026, 10, 23, 15, 40, tzinfo=IST)
    waiter.until(moment)
    assert said == [WAITING.format(moment=moment)] and "15:40 IST" in said[0] and "not a hang" in said[0]
    assert inner.waits == [moment]  # the wait itself is unchanged


def test_a_short_wait_a_past_moment_and_a_repeated_moment_say_nothing(announced):
    waiter, clock, inner, said = announced
    waiter.until(clock.now + timedelta(seconds=5))  # a part's 5-second servicing poll
    waiter.until(clock.now - timedelta(minutes=10))  # a run already past the step's time
    assert said == []
    moment = clock.now + timedelta(minutes=20)
    clock.now -= timedelta(minutes=1)  # a loop waiting towards one moment
    waiter.until(moment)
    clock.now -= timedelta(minutes=5)
    waiter.until(moment)
    assert len(said) == 1


def test_the_run_s_waiter_announces_its_waits(tmp_path, monkeypatch):
    from tests.e2e.harness import fixture_day

    day = fixture_day(tmp_path, monkeypatch)
    assert isinstance(day.runner().waiter, AnnouncedWaiter)
