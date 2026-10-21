"""A16's observer group (orchestrator's go, 16 Oct): members in order, each isolated, a hung member cut off at the
time limit, failures named by class only, and the recorder's rows and commit unaffected."""

import threading
import time as clock
from datetime import date, datetime, time

import pytest

from fno.intraday.observer import MarkObserver, MembersFailed
from fno.intraday.observer_group import MAX_LIMIT_SECONDS, ObserverGroup
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
    group = ObserverGroup([(Recording(log, "monitor"), 5), (Broken(), 5), (Recording(log, "poll"), 5)])
    with pytest.raises(MembersFailed) as failed:
        group.after_mark(date(2026, 10, 19), MARK, None, "good")
    assert [name for name, *_ in log] == ["monitor", "poll"]
    assert failed.value.names == ["Broken: PollDown"] and "never be printed" not in str(failed.value)


def test_a_hung_member_is_cut_off_at_the_limit_and_the_next_still_runs():
    log, hung = [], Hung()
    group = ObserverGroup([(hung, 0.2), (Recording(log, "poll"), 5)])
    started = clock.monotonic()
    with pytest.raises(MembersFailed) as failed:
        group.after_mark(date(2026, 10, 19), MARK, None, "good")
    assert clock.monotonic() - started < 2 and failed.value.names == ["Hung timed out"]
    assert [name for name, *_ in log] == ["poll"]
    hung.release.set()


def test_an_empty_group_and_members_in_time_raise_nothing():
    ObserverGroup([]).after_mark(date(2026, 10, 19), MARK, None, "good")
    log = []
    ObserverGroup([(Recording(log, "a"), 5)]).after_mark(date(2026, 10, 19), MARK, None, "missed")
    assert log == [("a", MARK, "missed")]


def test_each_member_has_its_own_limit_and_a_slow_member_inside_its_limit_finishes():
    log = []

    class Slow(MarkObserver):
        def after_mark(self, day, mark, document, status):
            clock.sleep(0.3)
            log.append("slow")

    hung = Hung()
    group = ObserverGroup([(Slow(), 2.0), (hung, 0.1), (Recording(log, "poll"), 5)])
    with pytest.raises(MembersFailed) as failed:
        group.after_mark(date(2026, 10, 19), MARK, None, "good")
    hung.release.set()
    assert failed.value.names == ["Hung timed out"] and log[0] == "slow" and log[1][0] == "poll"


@pytest.mark.parametrize("limit", [0, -1, MAX_LIMIT_SECONDS + 1])
def test_a_limit_outside_the_allowed_range_is_refused(limit):
    with pytest.raises(ValueError):
        ObserverGroup([(Recording([], "a"), limit)])


def test_in_the_recorder_a_failing_or_hung_member_never_stops_the_rows_or_the_commit(tmp_path):
    recorder, _, _, publisher, _ = build(tmp_path, FakeClock(ist(DAY, 10, 25)))
    log, hung = [], Hung()
    recorder.observer = ObserverGroup([(hung, 0.1), (Broken(), 5), (Recording(log, "poll"), 5)])
    outcomes = recorder.run(time(10, 35))
    lines = [line for o in outcomes for line in o.lines]
    assert any(line.startswith("mark observer failed at 10:30: Hung timed out, Broken: PollDown") for line in lines)
    assert not any("never be printed" in line for line in lines)
    assert {r["mark_ist"]: r["status"] for r in recorder.ledger.rows(DAY)}["10:30"] == "good"
    assert ("poll", ist(DAY, 10, 30), "good") in log and publisher.commits
    hung.release.set()


def test_the_composition_root_wires_a21s_poll_at_its_agreed_10_s_until_lm1_plugs_in_before_it():
    from fno.announcements_live.wiring import LazyAnnouncementsPoller
    from fno.intraday import wiring

    [(member, limit)] = wiring._observers(dry_run=False)
    assert isinstance(member, LazyAnnouncementsPoller) and not member.dry_run and limit == 10.0
