"""`python -m fno routine-log <begin|run|end|watch>` (story O13).

- begin: opens today's run of a routine and writes its `begin.json` to Drive (`logs/routines/<day>/<routine>/<run>/`).
- run --routine R --step S -- <command ...>: runs the command with its output shown live, writes the step's log file,
  and on a non-zero exit posts one #fno-desk line at once (the step, the exit code, the log's path and its last
  lines). Exits with the command's own code, so the routine reads it as before. `--last` also closes the run after
  the step, so a run whose session ends before its last command does (the desk's `daily run`) still gets `end.json`.
- end: writes `end.json` (`ok`, or `failed` with the failed steps) and closes the run.
- watch: the hourly check (routine-watch.yml): every expected run of today that is missing, stuck or failed, alerted
  once. Exit 1 when an alert could not be sent or Drive could not be read.
A Drive failure never stops a routine: the line "routine log NOT saved to Drive" is printed and the command still runs.
"""

from __future__ import annotations

import contextlib
import shlex

from ..alerts.sender import SENT
from .findings import failed_key
from .step_runner import last_lines, run_command
from .watch import LINES_SHOWN, alert_marker

FAILED_NOW = "Omenix F&O routine {routine}: step {step} failed (exit {code}). Log: Drive logs/routines/{path}\n{lines}"
LAST_NOTE = "closed after its last step {step} (exit {code})"
WATCH_FAILED = "Omenix F&O routine watcher could not read the logs in Drive: {error}"


def add_routine_log_parser(sub) -> None:
    p = sub.add_parser("routine-log", help="routine run logs in Drive and the routine watcher (story O13)")
    actions = p.add_subparsers(dest="action", required=True)
    begin = actions.add_parser("begin", help="open a routine's run log")
    begin.add_argument("--routine", required=True)
    begin.add_argument("--session", default="", help="the session's link, when known")
    begin.set_defaults(func=cmd_begin)
    run = actions.add_parser("run", help="run one command and log it")
    run.add_argument("--routine", required=True)
    run.add_argument("--step", required=True, help="a short name: lower-case letters, digits, hyphens")
    run.add_argument("--last", action="store_true", help="the routine's last step: close the run after it")
    run.add_argument("command", nargs="+", help="the command, after --")
    run.set_defaults(func=cmd_run)
    end = actions.add_parser("end", help="close a routine's run log")
    end.add_argument("--routine", required=True)
    end.add_argument("--note", default="", help="one line: the routine's result")
    end.set_defaults(func=cmd_end)
    watch = actions.add_parser("watch", help="alert missing, stuck and failed runs of today")
    watch.set_defaults(func=cmd_watch)


def cmd_begin(args, out=print, log=None) -> int:
    from .wiring import build_run_log

    run, problem = (log or build_run_log()).begin(args.routine, args.session)
    out(problem or f"routine log opened: {run.folder.path}")
    return 0


def cmd_run(args, out=print, log=None, sender=None, runner=run_command) -> int:
    from .run_log import StepResult
    from .wiring import build_run_log, build_sender

    log = log or build_run_log()
    started = log.clock()
    code, output = runner(args.command)
    result = StepResult(args.step, shlex.join(args.command), code, started, log.clock(), output)
    path, problem = log.step(args.routine, result)
    if problem:
        out(problem)
    if code != 0:
        _alert_failure(args.routine, args.step, code, path, output, log, sender or build_sender(), out)
    if getattr(args, "last", False):
        status, line = log.end(args.routine, LAST_NOTE.format(step=args.step, code=code))
        out(f"routine {args.routine}: {status}; {line}")
    return code


def _alert_failure(routine, step, code, path, output, log, sender, out) -> None:
    from .scrub import scrub

    lines = "\n".join(last_lines(scrub(output), LINES_SHOWN))
    outcome = sender.send(FAILED_NOW.format(routine=routine, step=step, code=code, path=path, lines=lines))
    out(outcome)
    run_folder = path.split("/steps/", 1)[0]
    if outcome == SENT:
        # without the marker the watcher alerts once more: never worse than silence
        with contextlib.suppress(Exception):
            log.store.put(alert_marker(log.clock().date(), failed_key(routine, run_folder.rsplit("/", 1)[-1])),
                          outcome.encode())  # fmt: skip


def cmd_end(args, out=print, log=None) -> int:
    from .wiring import build_run_log

    status, line = (log or build_run_log()).end(args.routine, args.note)
    out(f"routine {args.routine}: {status}; {line}")
    return 0


def cmd_watch(args, out=print, watcher=None, sender=None) -> int:
    from .wiring import build_sender, build_watcher

    sender = sender or build_sender()
    try:
        unsent = (watcher or build_watcher()).alert_new(sender, out)
    except Exception as error:  # noqa: BLE001 - the watcher's own failure is alerted, never silent
        out(sender.send(WATCH_FAILED.format(error=f"{type(error).__name__}: {error}")))
        return 1
    out("routine watch: done" if not unsent else f"routine watch: {unsent} alert(s) NOT sent")
    return 1 if unsent else 0
