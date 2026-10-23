"""Judge 542's must-fixes and pins: a run that dies late is found after midnight, secrets are scrubbed where they are
written and posted, a bad name never runs its command, the schedule and slot edges are fixed, signals keep the
shell's exit code."""

import argparse
from argparse import Namespace
from datetime import time

import pytest

from fno.routine_logs.cli import add_routine_log_parser, cmd_run, cmd_watch
from fno.routine_logs.findings import STUCK
from fno.routine_logs.schedule import FIRST_OF_MONTH, ROUTINES, TRADING_DAYS
from fno.routine_logs.step_runner import run_command
from fno.routine_logs.watch import RoutineWatcher

from .conftest import Clock, Sent, ist

TOKEN = "xoxb-" + "1234567890-abcdefghijkl"
PARTICIPANT_OI = next(spec for spec in ROUTINES if spec.name == "participant-oi")


def _watcher(store, now, specs=(PARTICIPANT_OI,)):
    return RoutineWatcher(store, specs, lambda day: day.day == 23, Clock(now))


def test_a_late_run_that_died_is_alerted_once_after_midnight(store):
    store.put("2026-10-23/participant-oi/171230-aaaaaa/begin.json", b"{}")
    assert _watcher(store, ist(23, 17)).findings() == []  # its 400 minutes end at 23:52
    sender = Sent()
    assert _watcher(store, ist(0, 17, day=24)).alert_new(sender, lambda _: None) == 0
    assert len(sender.texts) == 1 and "participant-oi (17:11 IST) started but has not finished" in sender.texts[0]
    [finding] = _watcher(store, ist(1, 17, day=24)).findings()
    assert finding.kind == STUCK and finding.day.day == 23
    assert _watcher(store, ist(1, 17, day=24)).alert_new(sender, lambda _: None) == 0 and len(sender.texts) == 1


def test_a_token_in_a_commands_output_is_scrubbed_in_the_drive_file_and_the_alert(run_log, store):
    run, _ = run_log.begin("daily-desk")
    sender = Sent()
    args = Namespace(routine="daily-desk", step="daily-run", last=False, command=["false"])
    cmd_run(args, out=lambda _: None, log=run_log, sender=sender, runner=lambda c: (1, f"auth {TOKEN} refused\n"))
    step_file = store.get(f"{run.folder.path}/steps/01-daily-run.log").decode()
    assert TOKEN not in step_file and "[removed: Slack token]" in step_file
    assert TOKEN not in sender.texts[0] and "[removed: Slack token]" in sender.texts[0]


def test_the_watchers_own_error_line_is_scrubbed():
    class Failing:
        def alert_new(self, sender, out):
            raise PermissionError(f"Drive refused {TOKEN}")

    sender = Sent()
    assert cmd_watch(Namespace(), out=lambda _: None, watcher=Failing(), sender=sender) == 1
    assert TOKEN not in sender.texts[0] and "[removed: Slack token]" in sender.texts[0]


@pytest.mark.parametrize(
    "bad", [["--routine", "daily-desk", "--step", "Daily_Run"], ["--routine", "../x", "--step", "s"]]
)
def test_a_bad_name_stops_before_the_command_runs(tmp_path, bad):
    parser = argparse.ArgumentParser()
    add_routine_log_parser(parser.add_subparsers(dest="command_name"))
    marker = tmp_path / "ran"
    with pytest.raises(SystemExit) as stopped:
        parser.parse_args(["routine-log", "run", *bad, "--", "touch", str(marker)])
    assert stopped.value.code == 2 and not marker.exists()


def test_the_schedule_matches_the_live_routines():
    """docs/stories/O13-routine-instructions.md section 1 (the live times of 23 Oct); a change is the owner's."""
    hourly = tuple(time(hour, 52) for hour in range(8, 15))
    expected = {
        "a16-backup": ((time(8, 22),), TRADING_DAYS, 185),
        "pre-open": ((time(8, 36),), TRADING_DAYS, 45),
        "morning-forecast": ((time(8, 38),), TRADING_DAYS, 40),
        "a16-recorder": (hourly, TRADING_DAYS, 160),
        "daily-desk": ((time(14, 5),), TRADING_DAYS, 150),
        "participant-oi": ((time(17, 11),), TRADING_DAYS, 400),
        "evening-forecast": ((time(19, 53),), TRADING_DAYS, 60),
        "participant-oi-sweep": ((time(7, 7),), FIRST_OF_MONTH, 60),
    }
    assert {spec.name: (spec.starts, spec.days, spec.max_minutes) for spec in ROUTINES} == expected


@pytest.mark.parametrize(("run", "missing"), [("142600-aaaaaa", False), ("142400-aaaaaa", True)])
def test_a_run_up_to_ten_minutes_early_belongs_to_its_slot(store, run, missing):
    desk = next(spec for spec in ROUTINES if spec.name == "daily-desk")
    late = desk.__class__("daily-desk", (time(14, 35),), TRADING_DAYS, 150)
    store.put(f"2026-10-23/daily-desk/{run}/end.json", b'{"failed_steps": []}')
    kinds = [finding.kind for finding in _watcher(store, ist(15, 0), (late,)).findings()]
    assert kinds == (["missing"] if missing else [])


def test_a_command_killed_by_a_signal_exits_with_the_shells_code():
    code, _ = run_command(["sh", "-c", "kill -TERM $$"], lambda _: None)
    assert code == 128 + 15
