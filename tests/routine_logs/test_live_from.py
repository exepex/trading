"""Judge 542 addendum 1: a routine is watched only from its `routine_logs.live_from` date, so the watcher is silent
until each routine's instructions log; and an alert sent before midnight is not sent again after it."""

from datetime import date, time

import pytest

from fno.config import load_app_config
from fno.routine_logs.schedule import ROUTINES, TRADING_DAYS, RoutineSpec
from fno.routine_logs.watch import RoutineWatcher
from fno.routine_logs.wiring import live_dates

from .conftest import LIVE, Clock, Sent, ist

DESK = RoutineSpec("daily-desk", (time(14, 5),), TRADING_DAYS, 150)


def _watcher(store, now, live, specs=(DESK,)):
    return RoutineWatcher(store, specs, lambda day: day.day == 23, Clock(now), live)


def test_a_routine_is_missed_only_from_its_live_date(store):
    assert _watcher(store, ist(15, 0), {"daily-desk": None}).findings() == []
    assert _watcher(store, ist(15, 0), {}).findings() == []
    assert _watcher(store, ist(15, 0), {"daily-desk": date(2026, 10, 24)}).findings() == []
    [finding] = _watcher(store, ist(15, 0), {"daily-desk": date(2026, 10, 23)}).findings()
    assert finding.kind == "missing" and finding.day == date(2026, 10, 23)


def test_the_real_config_names_every_routine_and_watches_none_yet(store):
    live = live_dates(load_app_config())
    assert set(live) == {spec.name for spec in ROUTINES}
    assert _watcher(store, ist(15, 0), live, ROUTINES).findings() == []  # the judge's probe: 26 false lines before


def test_a_failed_run_whose_step_file_never_reached_drive_is_still_alerted(store):
    store.put("2026-10-23/daily-desk/140512-aaaaaa/end.json", b'{"failed_steps": ["daily-run"]}')
    [finding] = _watcher(store, ist(16, 0), LIVE).findings()
    assert finding.kind == "failed" and finding.step == "daily-run" and finding.lines == ()


def test_an_alert_sent_before_midnight_is_not_sent_again_after_it(store):
    store.put("2026-10-23/daily-desk/140512-aaaaaa/end.json", b'{"failed_steps": ["daily-run"]}')
    sender = Sent()
    assert _watcher(store, ist(23, 17), LIVE).alert_new(sender, lambda _: None) == 0
    assert len(sender.texts) == 1
    assert _watcher(store, ist(0, 17, day=24), LIVE).alert_new(sender, lambda _: None) == 0
    assert len(sender.texts) == 1


def test_a_missing_alert_sent_before_midnight_is_not_sent_again_after_it(store):
    sender = Sent()
    _watcher(store, ist(23, 17), LIVE).alert_new(sender, lambda _: None)
    _watcher(store, ist(0, 17, day=24), LIVE).alert_new(sender, lambda _: None)
    assert len(sender.texts) == 1 and "(14:05 IST) did not start" in sender.texts[0]


def test_a_step_failing_after_midnight_marks_its_runs_day(run_log, store, clock):
    from argparse import Namespace

    from fno.routine_logs.cli import cmd_run
    from fno.routine_logs.watch import alert_marker

    clock.moment = ist(23, 50)
    run, _ = run_log.begin("participant-oi")
    clock.moment = ist(0, 20, day=24)
    args = Namespace(routine="participant-oi", step="watch", last=False, command=["false"])
    cmd_run(args, out=lambda _: None, log=run_log, sender=Sent(), runner=lambda c: (1, "absent\n"))
    assert store.get(alert_marker(date(2026, 10, 23), f"participant-oi-{run.folder.run}-failed")) is not None


def test_a_misspelt_routine_name_in_config_is_refused():
    with pytest.raises(ValueError, match="a16_recorder"):
        live_dates({"routine_logs": {"live_from": {"a16_recorder": "2026-10-24"}}})
