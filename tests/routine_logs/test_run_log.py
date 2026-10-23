import json
from argparse import Namespace

from fno.routine_logs.cli import cmd_run
from fno.routine_logs.run_log import RoutineRunLog, StepResult
from fno.routine_logs.run_state import RunStateFolder
from fno.routine_logs.scrub import scrub
from fno.routine_logs.step_runner import NOT_STARTED, run_command
from fno.routine_logs.watch import alert_marker

from .conftest import Sent, ist


def _step(label, code, output="hello\n"):
    return StepResult(label, "python -m fno daily run", code, ist(14, 6), ist(14, 9), output)


def test_a_run_writes_begin_each_step_and_end(run_log, store):
    run, problem = run_log.begin("daily-desk", "https://example.invalid/session")
    assert problem == ""
    path, problem = run_log.step("daily-desk", _step("daily-run", 0))
    assert problem == "" and path == f"{run.folder.path}/steps/01-daily-run.log"
    text = store.get(path).decode()
    assert "exit 0" in text and text.endswith("hello\n")
    status, line = run_log.end("daily-desk", "day done")
    end = json.loads(store.get(f"{run.folder.path}/end.json"))
    assert status == "ok" and end["status"] == "ok" and end["steps"] == 1 and line.endswith(run.folder.path)
    assert json.loads(store.get(f"{run.folder.path}/begin.json"))["routine"] == "daily-desk"
    assert run.folder.path.startswith("2026-10-23/daily-desk/140500-")


def test_a_failed_step_makes_the_run_failed_and_a_step_without_begin_opens_one(run_log, store):
    path, _ = run_log.step("pre-open", _step("record", 2))
    assert path.startswith("2026-10-23/pre-open/") and path.endswith("/steps/01-record.log")
    status, _ = run_log.end("pre-open")
    end = json.loads(store.get(path.split("/steps/")[0] + "/end.json"))
    assert status == "failed" and end["failed_steps"] == ["record"]


def test_a_drive_failure_never_stops_the_routine(tmp_path, clock):
    class Broken:
        def put(self, path, data):
            raise ConnectionError("down")

    log = RoutineRunLog(Broken(), RunStateFolder(tmp_path / "s"), clock)
    _, problem = log.begin("daily-desk")
    assert problem == "routine log NOT saved to Drive (begin): ConnectionError: down"
    _, problem = log.step("daily-desk", _step("daily-run", 0))
    assert "NOT saved" in problem


def test_secrets_are_removed_but_the_fno_channels_stay():
    token = "xoxb-" + "1234567890-abcdefghijkl"
    text = scrub(f"token {token} mail someone@example.com channel C0C89E8QCCD")
    assert token not in text and "someone@example.com" not in text and "C0C89E8QCCD" in text
    assert "[removed: Slack token]" in text


def test_the_runner_passes_output_through_and_returns_the_exit_code():
    seen = []
    code, output = run_command(["python3", "-c", "print('a'); raise SystemExit(3)"], seen.append)
    assert code == 3 and output == "a\n" and seen == ["a"]
    code, output = run_command(["no-such-command-o13"], seen.append)
    assert code == NOT_STARTED and "could not start" in output


def test_a_failed_command_alerts_at_once_and_marks_the_alert(run_log, store):
    sender, lines = Sent(), []
    args = Namespace(routine="daily-desk", step="daily-run", command=["python3", "-c", "raise SystemExit(1)"])
    code = cmd_run(args, out=lines.append, log=run_log, sender=sender,
                   runner=lambda command: (1, "boom: Groww refused\n"))  # fmt: skip
    assert code == 1 and len(sender.texts) == 1
    assert "step daily-run failed (exit 1)" in sender.texts[0] and "boom: Groww refused" in sender.texts[0]
    run = RunStateFolder(run_log.state.folder).load("daily-desk")
    assert store.get(alert_marker(ist(14, 5).date(), f"daily-desk-{run.folder.run}-failed")) is not None


def test_a_passing_command_sends_nothing(run_log):
    sender = Sent()
    args = Namespace(routine="daily-desk", step="setup", command=["true"])
    assert cmd_run(args, out=lambda _: None, log=run_log, sender=sender, runner=lambda c: (0, "ok\n")) == 0
    assert sender.texts == []


def test_the_last_step_closes_the_run_even_without_end(run_log, store):
    run, _ = run_log.begin("daily-desk")
    args = Namespace(routine="daily-desk", step="daily-run", last=True, command=["true"])
    assert cmd_run(args, out=lambda _: None, log=run_log, sender=Sent(), runner=lambda c: (0, "day done\n")) == 0
    end = json.loads(store.get(f"{run.folder.path}/end.json"))
    assert end["status"] == "ok" and "last step daily-run (exit 0)" in end["note"]
    assert RunStateFolder(run_log.state.folder).load("daily-desk") is None


def test_steps_finishing_at_once_are_all_counted(run_log):
    from concurrent.futures import ThreadPoolExecutor

    run_log.begin("pre-open")
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(lambda n: run_log.step("pre-open", _step(f"part-{n}", n % 2)), range(8)))
    run = RunStateFolder(run_log.state.folder).load("pre-open")
    assert run.steps == 8 and sorted(run.failed) == ["part-1", "part-3", "part-5", "part-7"]
