"""Story A19 criteria 7 and 10: the run loop, its flushes, its end, the overnight bridge and the coverage gap."""

from datetime import time, timedelta

import pytest

from fno.news.episodes import Episodes
from fno.news.memory import SeenMemory
from fno.news.polling import FeedPoller
from fno.news.runner import NewsRun, RunPlan
from fno.news.settings import Window
from fno.news.stale import StaleRule
from fno.news.window import PollingWindow
from tests.news.fakes import (
    HEADLINE,
    LINK,
    MARKETS,
    Alerts,
    Clock,
    Committer,
    MemoryLog,
    ScriptedSource,
    calendar,
    ist,
    item_xml,
    rss,
)

WINDOW = PollingWindow(Window(time(7), time(23)))
FEED = rss(item_xml(HEADLINE, LINK, "Fri, 16 Oct 2026 09:59:00 +0530"))


class Store:
    def __init__(self, fail_parts: int = 0):
        self.parts, self.snapshots, self.fail_parts = [], [], fail_parts

    def put_part(self, now, sequence, lines):
        if self.fail_parts:
            self.fail_parts -= 1
            raise ConnectionError("drive down")
        self.parts.append((now, sequence, list(lines)))

    def put_snapshot(self, now, sequence, memory):
        self.snapshots.append((now, sequence))


def make(start, bridge=False, max_run=timedelta(minutes=340), memory=None, store=None, committer=None, answers=None):
    clock = Clock(start)
    memory = memory or SeenMemory()
    log, alerts = MemoryLog(), Alerts()
    found = Episodes(log, alerts, clock, lambda _: None)
    source = ScriptedSource(MARKETS, answers or [FEED, None], clock)
    feeds = FeedPoller([source], memory, found, StaleRule(calendar()), "run-1")
    run = NewsRun(feeds, memory, store or Store(), found, committer or Committer(), RunPlan(WINDOW, bridge, max_run),
                  clock, clock.sleep, lambda _: None)  # fmt: skip
    return run, clock, source, log, alerts


def polls(store):
    return [line["polled_at"] for _, _, lines in store.parts for line in lines if line["line"] == "poll"]


def test_polls_every_5_minutes_flushes_every_15_with_heartbeats_and_stops_at_the_limit():
    store = Store()
    run, clock, source, *_ = make(ist(2026, 10, 16, 10, 0), max_run=timedelta(minutes=60), store=store)
    lasted = run.run()
    assert lasted == timedelta(minutes=60)
    assert source.calls == 12
    assert len(store.parts) == 4  # at 15, 30 and 45 minutes and at the end: heartbeats even with nothing new
    assert all(any(line["line"] == "poll" for line in lines) for _, _, lines in store.parts)
    assert len(store.snapshots) == 1  # at the end (the 2-hour one was not due)


def test_the_run_stops_when_the_window_closes_without_the_bridge():
    store = Store()
    run, clock, *_ = make(ist(2026, 10, 16, 22, 30), store=store)
    run.run()
    assert clock() == ist(2026, 10, 16, 23, 0)
    assert polls(store)[-1] == ist(2026, 10, 16, 22, 55).isoformat()


def test_bridge_keeps_a_run_alive_overnight_and_polls_first_at_0700():
    store = Store()
    run, clock, *_ = make(ist(2026, 10, 16, 22, 30), bridge=True, store=store)
    run.run()  # 340 minutes from 22:30 end at 04:10, still inside the closed night
    assert clock() == ist(2026, 10, 17, 4, 10)  # alive all night, so it can hand over to a successor
    assert max(polls(store)) == ist(2026, 10, 16, 22, 55).isoformat()  # nothing polled between 23:00 and 07:00
    second = Store()
    run, clock, *_ = make(ist(2026, 10, 17, 4, 10), bridge=True, store=second, max_run=timedelta(minutes=180))
    run.run()
    assert min(polls(second)) == ist(2026, 10, 17, 7, 0).isoformat()  # nothing at 06:59:59
    assert clock() == ist(2026, 10, 17, 7, 10)


def test_a_bridged_run_sleeps_to_its_end_when_the_window_opens_after_it():
    store = Store()
    run, clock, *_ = make(ist(2026, 10, 17, 0, 0), bridge=True, store=store, max_run=timedelta(minutes=340))
    assert run.run() == timedelta(minutes=340)  # 07:00 is past its 05:40 end: it sleeps to the end, then hands over
    assert polls(store) == []


@pytest.mark.parametrize(
    "last, gap", [(timedelta(minutes=15), False), (timedelta(minutes=15, seconds=1), True), (None, False)]
)
def test_coverage_gap_at_start(last, gap):
    start = ist(2026, 10, 16, 10, 0)
    memory = SeenMemory(last_heartbeat=(start - last).isoformat() if last else None)
    run, clock, source, log, alerts = make(start, memory=memory, max_run=timedelta(minutes=5))
    run.run()
    assert ("coverage_gap" in [r.kind for r in log.rows()]) is gap
    assert (len([a for a in alerts.sent if "coverage gap" in a]) == 1) is gap


def test_the_closed_night_is_never_a_gap():
    memory = SeenMemory(last_heartbeat=ist(2026, 10, 16, 22, 55).isoformat())
    run, clock, source, log, _ = make(ist(2026, 10, 17, 7, 0), memory=memory, max_run=timedelta(minutes=5))
    run.run()
    assert "coverage_gap" not in [r.kind for r in log.rows()]


def test_a_drive_failure_keeps_the_lines_for_the_next_flush():
    store = Store(fail_parts=1)
    run, clock, source, log, _ = make(ist(2026, 10, 16, 10, 0), max_run=timedelta(minutes=30), store=store)
    run.run()
    assert [r.kind for r in log.rows()] == ["drive_write", "drive_write_recovered"]
    assert polls(store)[0] == ist(2026, 10, 16, 10, 0).isoformat()  # the first poll was not lost


def test_a_commit_failure_is_an_episode():
    committer = Committer("news receipts NOT committed: push failed: rejected. Commit receipts/ by hand")
    run, clock, source, log, _ = make(ist(2026, 10, 16, 10, 0), committer=committer, max_run=timedelta(minutes=20))
    run.run()
    assert [r.kind for r in log.rows()] == ["receipt_commit"]


def test_an_exception_still_flushes_and_commits():
    store, committer = Store(), Committer()
    run, clock, source, *_ = make(ist(2026, 10, 16, 10, 0), store=store, committer=committer)
    real_poll, calls = run.poller.poll, []

    def poll_then_crash(now):
        calls.append(now)
        if len(calls) > 1:
            raise RuntimeError("bug")
        return real_poll(now)

    run.poller.poll = poll_then_crash
    with pytest.raises(RuntimeError):
        run.run()
    assert len(store.parts) == 1 and committer.calls == 1


def test_a_drive_failure_still_commits_its_failure_row():
    store, committer = Store(fail_parts=99), Committer()
    run, clock, source, log, _ = make(ist(2026, 10, 16, 10, 0), max_run=timedelta(minutes=15), store=store,
                                      committer=committer)  # fmt: skip
    run.run()
    assert [r.kind for r in log.rows()] == ["drive_write"]
    assert committer.calls == 3  # three tries at the end, each one committing (the row reaches the repository)
    assert run.saved is False


def test_the_last_flush_is_retried_until_saved():
    store = Store(fail_parts=2)
    run, clock, source, log, _ = make(ist(2026, 10, 16, 10, 0), max_run=timedelta(minutes=10), store=store)
    run.run()
    assert run.saved and len(store.parts) == 1
    assert [r.kind for r in log.rows()] == ["drive_write", "drive_write_recovered"]


def test_a_failed_commit_leaves_the_run_unsaved_and_tries_once_more_for_the_row():
    committer = Committer("news receipts NOT committed: push failed: rejected. Commit receipts/ by hand")
    run, clock, source, log, _ = make(ist(2026, 10, 16, 10, 0), committer=committer, max_run=timedelta(minutes=5))
    run.run()
    assert run.saved is False and committer.calls == 3 * 2  # each of the three last tries commits twice
    assert log.messages[0].endswith("(news receipts NOT committed: push failed)")  # short: no "by hand" hint


def test_a_healthy_run_closes_a_stopped_restart():
    run, clock, source, log, alerts = make(ist(2026, 10, 16, 10, 0), max_run=timedelta(minutes=20))
    run.episodes.fail("restart_stopped", "restart_stopped", "the run ended failure after 2.0 min: not restarted")
    run.run()
    assert [r.kind for r in log.rows()] == ["restart_stopped", "restart_stopped_recovered"]


def test_a_short_run_leaves_a_stopped_restart_open():
    run, clock, source, log, alerts = make(ist(2026, 10, 16, 10, 0), max_run=timedelta(minutes=9))
    run.episodes.fail("restart_stopped", "restart_stopped", "stopped")
    run.run()
    assert [r.kind for r in log.rows()] == ["restart_stopped"]


class SnapshotStore(Store):
    def __init__(self, fail_snapshots: int):
        super().__init__()
        self.fail_snapshots = fail_snapshots

    def put_snapshot(self, now, sequence, memory):
        if self.fail_snapshots:
            self.fail_snapshots -= 1
            raise ConnectionError("drive down")
        super().put_snapshot(now, sequence, memory)


def test_a_failed_snapshot_is_retried_at_the_next_flush_under_its_own_step():
    store = SnapshotStore(fail_snapshots=1)
    run, clock, source, log, _ = make(ist(2026, 10, 16, 10, 0), max_run=timedelta(minutes=140), store=store)
    run.run()
    assert [r.kind for r in log.rows()] == ["snapshot_write", "snapshot_write_recovered"]
    assert store.snapshots[0][0] == ist(2026, 10, 16, 12, 15)  # 2 h failed, retried 15 minutes later
