"""`python -m fno desk book1 [--day D]` and `python -m fno desk run [--day D]` (story E5): Book 1's decision for a day
(D2 through D3, committed), and E3's daily run for a day with Book 1's orders and exit rules. Paper only: nothing here
places an order. No routine starts them yet; run them by hand before 15:12 and from 14:58 IST."""

from __future__ import annotations

from datetime import date


def add_book1_command(actions) -> None:
    decide = actions.add_parser("book1", help="Book 1's decision for a day (D2 on its approved versions, committed)")
    decide.add_argument("--day", type=date.fromisoformat, help="the session day (default: today in IST)")
    decide.set_defaults(func=cmd_book1)


def add_run_command(actions) -> None:
    run = actions.add_parser("run", help="E3's daily run for a day: packs, decisions, capture, fills, exits (paper)")
    run.add_argument("--day", type=date.fromisoformat, help="the session day (default: today in IST)")
    run.set_defaults(func=cmd_run)


def cmd_book1(args) -> int:
    from ..config import load_app_config
    from ..models import now_ist
    from .book1_wiring import build_book1

    print(build_book1(load_app_config()).decide(args.day or now_ist().date()))
    return 0


def cmd_run(args) -> int:
    from ..config import load_app_config
    from ..desk.daily_wiring import build_daily_run
    from ..models import now_ist
    from .book1_wiring import build_book1_exit_rules, build_book1_orders

    cfg = load_app_config()
    log = build_daily_run(cfg, build_book1_orders(cfg), build_book1_exit_rules()).run(args.day or now_ist().date())
    for name, step in log.steps.items():
        print(f"{name}: {step['started_at']} -> {step['finished_at']}: {step['result']}")
    return 0
