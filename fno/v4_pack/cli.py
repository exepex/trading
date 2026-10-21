"""`python -m fno v4-pack release` (story G10 part 2): the catch-up and today's v4 release, then the receipts committed
and pushed with this run's own credentials (that push starts `.github/workflows/v4-fire.yml`). Research data only."""

from __future__ import annotations


def add_v4_pack_parser(subparsers) -> None:
    parser = subparsers.add_parser("v4-pack", help="protocol v4's daily pack and release record (G10)")
    actions = parser.add_subparsers(dest="v4_pack_cmd", required=True)
    actions.add_parser("release", help="catch up missed sessions, then release today's pack (after its capture)")
    parser.set_defaults(func=cmd_v4_pack)


def cmd_v4_pack(args) -> int:
    from ..config import load_config
    from ..models import now_ist
    from ..storage.data_wiring import build_receipt_committer
    from .wiring import build_release_run

    run, today = build_release_run(load_config()), now_ist().date()
    lines = run.run(today)
    print("\n".join(lines))
    print(build_receipt_committer().commit(f"v4 release {today}"))
    return 1 if run.refused else 0
