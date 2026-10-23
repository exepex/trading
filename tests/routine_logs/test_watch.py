import json
from datetime import time

from fno.routine_logs.findings import FAILED, MISSING, STUCK
from fno.routine_logs.schedule import FIRST_OF_MONTH, TRADING_DAYS, RoutineSpec
from fno.routine_logs.watch import RoutineWatcher

from .conftest import Clock, Sent, ist

DESK = RoutineSpec("daily-desk", (time(14, 5),), TRADING_DAYS, 150)
A16 = RoutineSpec("a16-recorder", (time(8, 52), time(9, 52)), TRADING_DAYS, 150)


def _run(store, routine, run, end=None, steps=()):
    base = f"2026-10-23/{routine}/{run}"
    store.put(f"{base}/begin.json", b"{}")
    for name, body in steps:
        store.put(f"{base}/steps/{name}", f"header\n---\n{body}".encode())
    if end is not None:
        store.put(f"{base}/end.json", json.dumps(end).encode())


def _watch(store, now, specs=(DESK,), session=True):
    """The 23rd is the session day under test; the 22nd (yesterday) and the 24th are closed unless a test says so."""
    return RoutineWatcher(store, specs, lambda day: session and day.day == 23, Clock(now))


def test_a_routine_with_no_log_after_its_grace_is_missing(store):
    assert _watch(store, ist(14, 19)).findings() == []  # still inside the 15-minute grace
    [finding] = _watch(store, ist(14, 21)).findings()
    assert finding.kind == MISSING and "did not start" in finding.alert_text()


def test_a_finished_ok_run_is_quiet(store):
    _run(store, "daily-desk", "140512-aaaaaa", {"failed_steps": []})
    assert _watch(store, ist(23, 0)).findings() == []


def test_a_failed_run_names_its_step_and_last_lines(store):
    _run(store, "daily-desk", "140512-aaaaaa", {"failed_steps": ["daily-run"]},
         [("01-setup.log", "ok"), ("02-daily-run.log", "line\nGrowwAPIException 429")])  # fmt: skip
    [finding] = _watch(store, ist(16, 0)).findings()
    assert finding.kind == FAILED and finding.step == "daily-run"
    assert "GrowwAPIException 429" in finding.alert_text()


def test_an_unfinished_run_past_its_time_is_stuck_at_its_last_step(store):
    _run(store, "daily-desk", "140512-aaaaaa", steps=[("01-setup.log", "ok"), ("02-daily-run.log", "waiting")])
    assert _watch(store, ist(16, 0)).findings() == []  # within its 150 minutes
    [finding] = _watch(store, ist(16, 40)).findings()
    assert finding.kind == STUCK and finding.step == "02-daily-run" and "waiting" in finding.alert_text()


def test_each_hourly_slot_needs_its_own_run(store):
    _run(store, "a16-recorder", "085201-aaaaaa", {"failed_steps": []})
    [finding] = _watch(store, ist(10, 30), (A16,)).findings()
    assert finding.kind == MISSING and finding.start == time(9, 52)


def test_closed_days_and_monthly_routines(store):
    assert _watch(store, ist(23, 0), session=False).findings() == []
    monthly = RoutineSpec("participant-oi-sweep", (time(7, 7),), FIRST_OF_MONTH, 60)
    assert _watch(store, ist(9, 0), (monthly,)).findings() == []  # the 23rd is not the 1st


def test_each_finding_is_alerted_once(store):
    sender = Sent()
    watcher = _watch(store, ist(14, 30))
    assert watcher.alert_new(sender, lambda _: None) == 0 and len(sender.texts) == 1
    assert watcher.alert_new(sender, lambda _: None) == 0 and len(sender.texts) == 1


def test_an_unsent_alert_is_counted_and_tried_again(store):
    sender = Sent("alert NOT sent: no token")
    watcher = _watch(store, ist(14, 30))
    assert watcher.alert_new(sender, lambda _: None) == 1
    assert watcher.alert_new(sender, lambda _: None) == 1 and len(sender.texts) == 2
