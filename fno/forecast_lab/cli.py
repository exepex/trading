"""`python -m fno lab close [--day D]` (story FL1-1): the 15:45 report to #fno-forecast, run by O1's `lab_close` step.
Exit 0 when the report was posted or there was nothing to post (a closed day, an already-posted rerun); exit 1 when it
was not posted, so O1's `Alerted` alerts the failure once (the command never alerts its own failure)."""

from __future__ import annotations

from datetime import date


def add_lab_parser(subparsers) -> None:
    p = subparsers.add_parser("lab", help="FL1: the forecast lab's 15:45 report to #fno-forecast")
    p.add_argument("action", choices=("close",))
    p.add_argument("--day", type=date.fromisoformat, default=None)
    p.set_defaults(func=cmd_lab)


def cmd_lab(args, out=print) -> int:
    from ..models import now_ist
    from .wiring import build_lab_close

    result = build_lab_close().run(args.day or now_ist().date())
    for line in result.lines:
        out(line)
    return 1 if result.failed else 0
