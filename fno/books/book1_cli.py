"""`python -m fno desk book1 [--day D]` and `python -m fno desk run [--day D]` (story E5): Book 1's decision for a day
(D2 through D3, committed), and E3's daily run for a day with Book 1's orders and exit rules. Paper only: nothing here
places an order. No routine starts them yet; run them by hand before 15:12 and from 14:58 IST."""

from __future__ import annotations

from datetime import date

NOT_COMMITTED = (
    "F&O Book 1 {day}: decision NOT committed: {reason}. It is not public, so it is not on time unless pushed before "
    "E3's deadline, and a daily run in this checkout stops at its first commit until this is resolved. {fix}"
)
FIX = "Fix: remove the cause, then rerun `fno desk book1` (it commits the recorded decision, never a new one)"


def add_book1_command(actions) -> None:
    decide = actions.add_parser("book1", help="Book 1's decision for a day (D2 on its approved versions, committed)")
    decide.add_argument("--day", type=date.fromisoformat, help="the session day (default: today in IST)")
    decide.add_argument("--commit-run", metavar="RUN_ID", help="commit a run on disk only, as recorded (story E5b)")
    decide.set_defaults(func=cmd_book1)


def add_run_command(actions) -> None:
    run = actions.add_parser("run", help="E3's daily run for a day: packs, decisions, capture, fills, exits (paper)")
    run.add_argument("--day", type=date.fromisoformat, help="the session day (default: today in IST)")
    run.set_defaults(func=cmd_run)


def cmd_book1(args) -> int:
    """A failed commit gives one alert, the same line printed and exit code 1, never a traceback (story E5b)."""
    from ..composition import build_alert_sender
    from ..config import load_app_config
    from ..desk.daily_ports import CommitFailed
    from ..desk.pending_commit import PendingChanged
    from ..models import now_ist
    from .book1 import CommitRunRefused
    from .book1_wiring import build_book1

    day, book1 = args.day or now_ist().date(), build_book1(load_app_config())
    try:
        print(book1.commit_run(day, args.commit_run) if args.commit_run else book1.decide(day))
    except CommitRunRefused as refused:
        print(refused)
        return 1
    except CommitFailed as failed:
        fix = "" if isinstance(failed, PendingChanged) else FIX
        text = NOT_COMMITTED.format(day=day, reason=failed, fix=fix).rstrip(" ")
        build_alert_sender().send(text)
        print(text)
        return 1
    return 0


def cmd_run(args) -> int:
    from ..config import load_app_config
    from ..desk.daily_run import RunStopped
    from ..desk.daily_wiring import build_daily_run
    from ..models import now_ist
    from .book1_wiring import build_book1_exit_rules, build_book1_orders

    cfg = load_app_config()
    try:
        log = build_daily_run(cfg, build_book1_orders(cfg), build_book1_exit_rules()).run(args.day or now_ist().date())
    except RunStopped as stopped:
        print(stopped)
        return 1
    for name, step in log.steps.items():
        print(f"{name}: {step['started_at']} -> {step['finished_at']}: {step['result']}")
    return 0
