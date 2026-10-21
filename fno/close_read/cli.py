"""`python -m fno closes read [--recheck]` (story A4h), run by O1's `close_read` (15:40) and `close_recheck` (16:00)
steps after `lab_close`; a hand run the same evening counts too (the NSE stamp decides, not the clock)."""

from __future__ import annotations

from .constants import READ, RECHECK


def add_closes_parser(subparsers) -> None:
    p = subparsers.add_parser("closes", help="A4h: today's index closes read from NSE after 15:30 (provisional)")
    p.add_argument("action", choices=("read",))
    p.add_argument("--recheck", action="store_true", help="the 16:00 second read, compared with the first")
    p.set_defaults(func=cmd_closes)


def cmd_closes(args) -> int:
    from .wiring import build_close_reader

    return build_close_reader().run(RECHECK if args.recheck else READ)
