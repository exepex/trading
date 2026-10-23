"""`python -m fno margins nse-span` (story A14's daily margin rows) and `margins stress-factor` (story A14c's stress
factor recompute), both from NSE's archived SPAN files (research only); `margins move`: O9b step 2's move of the
committed margins table and evidence CSVs into Drive, each read back equal."""

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
    move = actions.add_parser("move", help="move the committed margins table and evidence CSVs into Drive (O9b)")
    move.set_defaults(func=cmd_margins_move)


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


def cmd_margins_move(args) -> int:
    from ..config import load_app_config
    from ..storage.moving import MoveRefused
    from .wiring import move_margins_to_drive

    try:
        print("\n".join(move_margins_to_drive(load_app_config(args.config))))
    except (MoveRefused, RuntimeError, OSError) as exc:  # Drive refused, settings missing, a file missing
        print(f"margins move stopped (nothing overwritten): {exc}")
        return 1
    print("commit receipts/data/margins/ (the rows are evidence once their receipts are committed)")
    return 0
