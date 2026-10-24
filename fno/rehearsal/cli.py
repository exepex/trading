"""`python -m fno rehearse check` (story REH1a, judge 557): the guard, run in a process started through the package's
real entry point with the mode set, so the replay clock and the HTTP guard it installs are what is checked. Prints
one line per problem and exits 1 on any; prints nothing and exits 0 when the rehearsal is safe."""

from __future__ import annotations

NOT_REHEARSING = "rehearse check: FNO_REHEARSAL is not set: nothing to check"


def add_rehearse_parser(subparsers) -> None:
    rehearse = subparsers.add_parser("rehearse", help="story REH1: a recorded day replayed safely")
    actions = rehearse.add_subparsers(dest="rehearse_cmd", required=True)
    actions.add_parser("check", help="the rehearsal guard, inside a rehearsing process").set_defaults(func=cmd_check)


def cmd_check(args, out=print) -> int:
    from .guard import problems
    from .mode import rehearsal
    from .process_checks import process_problems

    mode = rehearsal()
    if mode is None:
        out(NOT_REHEARSING)
        return 1
    found = process_problems(mode) + problems()
    for line in found:
        out(line)
    return 1 if found else 0
