"""`python -m fno health capture-failed --run-id <id>` (story O10): run by the capture watcher (`capture-watch.yml`)
when a watched workflow's run did not succeed. It appends the run's one row to the capture-error log (never twice for
the same run) and posts one #fno-desk line only when the run cannot have posted its own (cancelled or timed out).
Exit 1 when GitHub could not be read or a needed line was not accepted, so the watcher's own alert speaks."""

from __future__ import annotations

ALREADY = "already recorded: {url}"
SUCCEEDED = "run {run_id} succeeded: nothing to record"


def add_capture_parser(actions) -> None:
    failed = actions.add_parser("capture-failed", help="record a failed capture run and alert if it posted nothing")
    failed.add_argument("--run-id", type=int, required=True, help="the watched workflow run's ID")
    failed.set_defaults(func=cmd_capture_failed)


def cmd_capture_failed(args, out=print, runs=None, log=None, alerts=None) -> int:
    from ..alerts.sender import SENT
    from .run_failures import RunSourceError, alert_text, capture_error, needs_alert
    from .wiring import build_capture_error_log, build_run_source

    runs, log = runs or build_run_source(), log or build_capture_error_log()
    try:
        error = capture_error(*runs.run(args.run_id))
    except RunSourceError as problem:
        out(f"capture-failed: {problem}")
        return 1
    if error is None:
        out(SUCCEEDED.format(run_id=args.run_id))
        return 0
    if log.has_run(error.run_url):
        out(ALREADY.format(url=error.run_url))
        return 0
    log.append(error)
    out(",".join(error.row()))
    if not needs_alert(error):
        return 0
    sent = (alerts or _sender()).send(alert_text(error))
    out(sent)
    return int(sent != SENT)


def _sender():
    from ..composition import build_alert_sender

    return build_alert_sender()
