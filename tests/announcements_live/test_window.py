"""The window, the clock checks, episodes and isolation (story A21 part 2, criteria 10 and 11)."""

import time as wall

import pytest

from fno.announcements_live.reading import NO_POLL, coverage
from fno.announcements_live.source import PollFailed
from fno.intraday.observer import MarkObserver
from fno.intraday.observer_group import ObserverGroup

from .helpers import DAY, Clock, Source, at, item, poller


def run_marks(tmp_path, answers, marks, start="09:15"):
    clock = Clock(at(start))
    run, failures, alerts = poller(tmp_path, Source(clock, *answers), clock, "20261019T034500Z-aaaaaa")
    for mark in marks:
        clock.now = at(mark)
        run.after_mark(DAY, at(mark), None, "good")
    return run, failures, alerts


def test_the_first_and_last_window_marks_poll_and_the_next_does_not(tmp_path):
    run, failures, _ = run_marks(tmp_path, [[item("1")], [item("1")]], ["09:15", "14:00", "14:15"])
    assert run.source.calls == 2 and failures.rows == []
    assert dict(coverage(DAY, run.days.load(DAY).polls))["14:00"] == "polled ok"


def test_a_day_with_no_ok_poll_records_the_missed_window_once(tmp_path):
    run, failures, alerts = run_marks(tmp_path, [], ["14:15", "14:30"], start="14:15")
    assert failures.kinds() == ["missed_window"] and len(alerts.sent) == 1 and run.source.calls == 0


@pytest.mark.parametrize(("first_ok", "kinds"), [("10:00", []), ("10:15", ["no_poll_by_1000"])])
def test_no_ok_poll_by_the_10_00_mark_alerts(tmp_path, first_ok, kinds):
    marks = ["10:00", "10:15"]
    answers = [[item("1")], [item("1")]] if first_ok == "10:00" else [PollFailed("refused_403"), [item("1")]]
    _, failures, _ = run_marks(tmp_path, answers, marks, start="10:00")
    assert [k for k in failures.kinds() if k == "no_poll_by_1000"] == kinds


@pytest.mark.parametrize(("gap_seconds", "stale"), [(3600, False), (3601, True)])
def test_the_last_ok_poll_60_minutes_before_a_mark_is_clean_and_one_second_more_stale(tmp_path, gap_seconds, stale):
    clock = Clock(at("11:00"))
    run, failures, _ = poller(tmp_path, Source(clock, [item("1")], PollFailed("timeout")), clock,
                              "20261019T053000Z-bbbbbb")  # fmt: skip
    clock.now = at("11:00", -1)  # the ok poll's request leaves at 11:00:00
    run.after_mark(DAY, at("11:00"), None, "good")
    mark = at("11:00", gap_seconds)
    clock.now = mark
    run.after_mark(DAY, mark, None, "good")
    assert ("stale" in failures.kinds()) == stale


def test_three_failed_polls_are_one_episode_and_an_ok_poll_recovers(tmp_path):
    answers = [PollFailed("refused_403"), PollFailed("refused_429"), PollFailed("timeout"), [item("1")]]
    run, failures, alerts = run_marks(tmp_path, answers, ["09:15", "09:30", "09:45", "10:00"])
    assert failures.kinds() == ["refused_403"] and len(alerts.sent) == 2 and "recovered at 10:00" in alerts.sent[1]
    statuses = [p["status"] for p in run.days.load(DAY).polls]
    assert statuses == ["failed", "failed", "failed", "ok"]


def test_coverage_names_every_window_mark_and_shows_gaps(tmp_path):
    run, _, _ = run_marks(tmp_path, [[item("1")]], ["10:00"], start="10:00")
    lines = coverage(DAY, run.days.load(DAY).polls)
    assert len(lines) == 20 and lines[0] == ("09:15", NO_POLL) and dict(lines)["10:00"] == "polled ok"
    assert coverage(DAY, []) == [(mark, NO_POLL) for mark, _ in lines]


def test_an_item_without_seq_id_is_refused_and_the_others_kept(tmp_path):
    bad = item("2")
    bad.pop("seq_id")
    run, failures, _ = run_marks(tmp_path, [[item("1"), bad]], ["10:00"], start="10:00")
    assert run.days.load(DAY).seen == {"1"} and failures.kinds() == ["item_refused"]


def test_a_drive_failure_claims_no_item_and_the_next_poll_records_it_later(tmp_path):
    clock = Clock(at("10:00"))
    run, failures, _ = poller(tmp_path, Source(clock, [item("1")], [item("1")]), clock, "20261019T043000Z-cccccc")

    class Down:
        def write(self, day, mark, rows):
            raise OSError("Drive is down")

    good, run.items = run.items, Down()
    run.after_mark(DAY, at("10:00"), None, "good")
    assert "store_failed" in failures.kinds() and "1" not in run._states[DAY].seen
    run.items = good
    clock.now = at("10:15")
    run.after_mark(DAY, at("10:15"), None, "good")
    [row] = run.days.load(DAY).items
    assert row["first_seen_at"] > at("10:15").isoformat()  # later than the true sighting: safe for a cutoff


class Slow(MarkObserver):
    def after_mark(self, day, mark, document, status):
        wall.sleep(1.0)


class Raising(MarkObserver):
    def after_mark(self, day, mark, document, status):
        raise RuntimeError("planted")


class Called(MarkObserver):
    def __init__(self):
        self.calls = 0

    def after_mark(self, day, mark, document, status):
        self.calls += 1


@pytest.mark.parametrize("member", [Slow(), Raising()])
def test_a_slow_or_failing_poll_never_stops_lm1_or_the_recorder(member):
    lm1 = Called()
    group = ObserverGroup(((lm1, 1.0), (member, 0.2)))
    with pytest.raises(Exception) as failed:  # the group names the member; A16's notify turns it into one line
        group.after_mark(DAY, at("10:00"), None, "good")
    assert lm1.calls == 1 and type(member).__name__ in str(failed.value.names)
