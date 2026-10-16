"""`python -m fno daily run [--day YYYY-MM-DD]` (story O1): the whole desk day in one command, ending on one line
("day done", "day done with problems: <steps>", or E3's stop line with "no card today"). Paper only: never places,
modifies or cancels an order."""

from __future__ import annotations

from datetime import date


def add_daily_parser(subparsers) -> None:
    daily = subparsers.add_parser("daily", help="the desk's day: weather, v4 forecasts, quotes, desk, card (O1)")
    actions = daily.add_subparsers(dest="daily_cmd", required=True)
    run = actions.add_parser("run", help="run the day's steps in order, each recorded in journal/runs/<date>.json")
    run.add_argument("--day", type=date.fromisoformat, help="the session day (default: today in IST)")
    run.set_defaults(func=cmd_daily_run)


def cmd_daily_run(args, out=print) -> int:
    from ..config import load_app_config
    from ..models import now_ist
    from .wiring import build_day_runner

    code, line = build_day_runner(load_app_config()).run(args.day or now_ist().date())
    out(line)
    return code
