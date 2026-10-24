"""`python -m fno v4-pack release` (story G10 part 2; G10 completion, criterion 4): the catch-up and today's v4 release.
In the daily run its step commits the receipts with the run's one committer; by hand, `--commit` commits and pushes
them with this run's own credentials (that push starts `.github/workflows/v4-fire.yml` once G11 lands it). Exit 1 when
the release failed: a refused write, no ended capture yet, or a `system_late` today (decision D3). Research only."""

from __future__ import annotations


def add_v4_pack_parser(subparsers) -> None:
    parser = subparsers.add_parser("v4-pack", help="protocol v4's daily pack and release record (G10)")
    actions = parser.add_subparsers(dest="v4_pack_cmd", required=True)
    release = actions.add_parser(
        "release", help="catch up missed sessions, then release today's pack (after its capture)"
    )
    release.add_argument("--commit", action="store_true", help="commit and push the receipts (by hand only)")
    parser.set_defaults(func=cmd_v4_pack)


def cmd_v4_pack(args) -> int:
    from ..config import load_config
    from ..models import now_ist
    from .wiring import build_release_run

    run, today = build_release_run(load_config()), now_ist().date()
    print("\n".join(run.run(today)))
    if args.commit:
        from ..storage.data_wiring import build_receipt_committer

        print(build_receipt_committer().commit(f"v4 release {today}"))
    return 1 if run.failed else 0
