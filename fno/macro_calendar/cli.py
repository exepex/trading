"""`python -m fno macro-calendar [--day D]`: release-date snapshots of MOSPI's and the Fed's calendars (story A20c)."""

from __future__ import annotations

from datetime import date


def add_macro_calendar_parser(subparsers) -> None:
    p = subparsers.add_parser("macro-calendar", help="snapshot the macro release calendars to Drive (A20c)")
    p.add_argument("--day", type=date.fromisoformat, help="YYYY-MM-DD the run is for (default: today, IST)")
    p.set_defaults(func=cmd_macro_calendar)


def cmd_macro_calendar(args) -> int:
    from ..models import now_ist
    from .wiring import build_macro_calendar_job

    return build_macro_calendar_job().run(args.day or now_ist().date())
