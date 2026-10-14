"""`python -m fno margins nse-span`: story A14's daily margin rows from NSE's archived SPAN files (research only)."""

from __future__ import annotations


def add_margins_parser(subparsers) -> None:
    margins = subparsers.add_parser("margins", help="C2's margin inputs from NSE (story A14)")
    actions = margins.add_subparsers(dest="margins_cmd", required=True)
    span = actions.add_parser("nse-span", help="append each session's margins per lot from its SPAN file in Drive")
    span.add_argument("--due-day", action="store_true", help="only print the latest session whose file is out")
    span.set_defaults(func=cmd_margins_nse_span)


def cmd_margins_nse_span(args) -> int:
    from ..config import load_app_config
    from .wiring import build_nse_margin_job, due_day

    if args.due_day:
        print(due_day().isoformat())
        return 0
    return build_nse_margin_job(load_app_config(args.config)).run()
