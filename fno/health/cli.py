"""`python -m fno health check [--at <IST time>] [--dry-run]` (story O8). Prints the per-session table to the job's log,
posts one message to #fno-desk and appends its own run row (a failed run too, with its error type). A dry run prints the
message and changes nothing. A broken check posts "health check FAILED: <error type>" and exits 1; so does a message
Slack did not accept, so a revoked token turns the job red instead of going quiet."""

from __future__ import annotations

from datetime import datetime


def ist_time(text: str) -> datetime:
    """An ISO time; one without an offset is read as IST."""
    from ..models import IST

    moment = datetime.fromisoformat(text)
    return moment if moment.tzinfo else moment.replace(tzinfo=IST)


def _record_posted() -> None:
    """`posted=true` in the step's outputs (Actions); anything that stops before this leaves the workflow's own
    failure line to speak, so a crash at import or a sender that cannot be built is never silent."""
    import os

    from ..constants import ENV_GITHUB_OUTPUT

    path = os.environ.get(ENV_GITHUB_OUTPUT)
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("posted=true\n")


def add_health_parser(subparsers) -> None:
    parser = subparsers.add_parser("health", help="the daily health check of every daily job (story O8)")
    actions = parser.add_subparsers(dest="health_cmd", required=True)
    check = actions.add_parser("check", help="check the sessions of the window and post one summary to #fno-desk")
    check.add_argument("--at", type=ist_time, help="the run time (default now; no offset means IST)")
    check.add_argument("--dry-run", action="store_true", help="print the message; post and record nothing")
    parser.set_defaults(func=cmd_health)


def cmd_health(args, out=print) -> int:
    from ..alerts.sender import SENT
    from ..composition import build_alert_sender
    from ..config import load_app_config
    from ..models import IST, now_ist
    from .report import FAILED, message, table, verdict
    from .wiring import build_health_check, build_run_record

    started = now_ist()
    alerts = None if args.dry_run else build_alert_sender()
    try:
        check = build_health_check(load_app_config())
        run = check.run(args.at or started)
        text, result, code = message(run), verdict(run), 0
        for line in table(run):
            out(line)
    except Exception as error:  # the one place a broken check must still be heard
        text = result = FAILED.format(error=type(error).__name__)
        code = 1
    out(text)
    if alerts:
        sent = alerts.send(text)
        out(sent)
        if sent == SENT:
            _record_posted()  # the workflow's own alert stays quiet only after this (judge 240)
        build_run_record().append((args.at or started).astimezone(IST).date(), started, now_ist(), result)
        if sent == SENT and not code and run.warnings:
            check.horizon.mark()  # once only: a warning Slack accepted is never repeated for this calendar
        code = code or int(sent != SENT)
    return code
