"""A16's observer group (orchestrator's go, 16 Oct): members in order, each isolated, a hung member cut off at the
time limit, failures named by class only, and the recorder's rows and commit unaffected."""

import threading
import time as clock
from datetime import date, datetime, time

import pytest

from fno.intraday.observer import MarkObserver, MembersFailed
from fno.intraday.observer_group import MEMBER_TIME_LIMIT_SECONDS, ObserverGroup
from tests.intraday.fakes import DAY, FakeClock, build, ist

MARK = datetime(2026, 10, 19, 10, 30)


class Recording(MarkObserver):
    def __init__(self, log, name):
        self.log, self.name = log, name

    def after_mark(self, day, mark, document, status):
        self.log.append((self.name, mark, status))


class PollDown(Exception):
    pass


class Broken(MarkObserver):
    def after_mark(self, day, mark, document, status):
        raise PollDown("a message that must never be printed")


class Hung(MarkObserver):
    def __init__(self):
        self.release = threading.Event()

    def after_mark(self, day, mark, document, status):
        self.release.wait(30)


def test_members_run_in_order_and_a_failure_never_skips_the_next():
    log = []
    group = ObserverGroup([Recording(log, "monitor"), Broken(), Recording(log, "poll")])
    with pytest.raises(MembersFailed) as failed:
        group.after_mark(date(2026, 10, 19), MARK, None, "good")
    assert [name for name, *_ in log] == ["monitor", "poll"]
    assert failed.value.names == ["Broken: PollDown"] and "never be printed" not in str(failed.value)


def test_a_hung_member_is_cut_off_at_the_limit_and_the_next_still_runs():
    log, hung = [], Hung()
    group = ObserverGroup([hung, Recording(log, "poll")], limit_seconds=0.2)
    started = clock.monotonic()
    with pytest.raises(MembersFailed) as failed:
        group.after_mark(date(2026, 10, 19), MARK, None, "good")
    assert clock.monotonic() - started < 2 and failed.value.names == ["Hung timed out"]
    assert [name for name, *_ in log] == ["poll"]
    hung.release.set()


def test_an_empty_group_and_members_in_time_raise_nothing():
    ObserverGroup([]).after_mark(date(2026, 10, 19), MARK, None, "good")
    log = []
    ObserverGroup([Recording(log, "a")]).after_mark(date(2026, 10, 19), MARK, None, "missed")
    assert log == [("a", MARK, "missed")]


def test_the_limit_is_the_agreed_per_mark_budget():
    assert MEMBER_TIME_LIMIT_SECONDS == 10.0


def test_in_the_recorder_a_failing_or_hung_member_never_stops_the_rows_or_the_commit(tmp_path):
    recorder, _, _, publisher, _ = build(tmp_path, FakeClock(ist(DAY, 10, 25)))
    log, hung = [], Hung()
    recorder.observer = ObserverGroup([hung, Broken(), Recording(log, "poll")], limit_seconds=0.1)
    outcomes = recorder.run(time(10, 35))
    lines = [line for o in outcomes for line in o.lines]
    assert any(line.startswith("mark observer failed at 10:30: Hung timed out, Broken: PollDown") for line in lines)
    assert not any("never be printed" in line for line in lines)
    assert {r["mark_ist"]: r["status"] for r in recorder.ledger.rows(DAY)}["10:30"] == "good"
    assert ("poll", ist(DAY, 10, 30), "good") in log and publisher.commits
    hung.release.set()


def test_the_composition_root_wires_an_empty_group_until_lm1_and_a21_plug_in():
    from fno.intraday import wiring

    assert wiring._observers() == ()
