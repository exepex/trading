"""`python -m fno margins nse-span` (story A14's daily margin rows) and `margins stress-factor` (story A14c's stress
factor recompute), both from NSE's archived SPAN files, and `margins stress-broker-check` (A14c part 2: the day's rows
against Groww's read-only margin calculator, in O1's routine only). Research only."""

from __future__ import annotations


def add_margins_parser(subparsers) -> None:
    margins = subparsers.add_parser("margins", help="C2's margin inputs from NSE (story A14)")
    actions = margins.add_subparsers(dest="margins_cmd", required=True)
    span = actions.add_parser("nse-span", help="append each session's margins per lot from its SPAN file in Drive")
    span.add_argument("--due-day", action="store_true", help="only print the latest session whose file is out")
    span.set_defaults(func=cmd_margins_nse_span)
    stress = actions.add_parser("stress-factor", help="recompute the stress factor k from the archive (story A14c)")
    stress.add_argument(
        "--full", action="store_true", help="read every session since 2 Jan 2020, not only the new ones"
    )
    stress.add_argument(
        "--approve-fall", metavar="COMMIT", help="apply a lower factor: the owner's DESK_DECISIONS commit"
    )
    stress.set_defaults(func=cmd_margins_stress_factor)
    check = actions.add_parser(
        "stress-broker-check", help="check today's A14 rows against Groww's read-only margin calculator (A14c part 2)"
    )
    check.set_defaults(func=cmd_margins_stress_broker_check)


def cmd_margins_nse_span(args) -> int:
    from ..config import load_app_config
    from .wiring import build_nse_margin_job, due_day

    if args.due_day:
        print(due_day().isoformat())
        return 0
    return build_nse_margin_job(load_app_config(args.config)).run()


def cmd_margins_stress_factor(args) -> int:
    from ..config import load_app_config
    from .wiring import build_stress_factor_run

    return build_stress_factor_run(load_app_config(args.config)).run(args.full, args.approve_fall)


def cmd_margins_stress_broker_check(args) -> int:
    from ..config import load_app_config
    from .broker_wiring import build_broker_check

    return build_broker_check(load_app_config(args.config)).run()
