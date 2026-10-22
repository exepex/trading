"""`python -m fno data-hosts --day D` (story A9c): every librarian dataset's file for one day from both NSE hosts,
compared by SHA-256; read-only, stores nothing."""

from __future__ import annotations

from datetime import date


def add_hosts_parser(subparsers) -> None:
    p = subparsers.add_parser("data-hosts", help="A9c: one day's NSE files from both archive hosts, compared")
    p.add_argument("--day", type=date.fromisoformat, required=True, help="YYYY-MM-DD of the files to compare")
    p.set_defaults(func=cmd_data_hosts)


def cmd_data_hosts(args) -> int:
    from .host_check import compare_hosts
    from .source_lists import LIBRARIAN_DATASETS
    from .wiring import build_nse_source

    return compare_hosts(LIBRARIAN_DATASETS.values(), args.day, build_nse_source)
