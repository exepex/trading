"""`python -m fno global-cues <fill|check|verify> [--cue NAME ...] [--from YYYY-MM-DD] [--to YYYY-MM-DD]` (story A17).

- fill: downloads each cue's files, archives them in the owner's Drive, extends the tables, rewrites the checks. The
  first run back-fills from each source's first date; later runs look back 31 days. Not scheduled.
- check: rewrites the checks from the committed tables (no network).
- verify: recomputes every table row from the archived copy it names (read-only).
Commit `research/data/global-cues/` and `research/data/manifests/global-cues/` after a run.
"""

from __future__ import annotations

from datetime import date

from ..models import now_ist


def add_global_cues_parser(subparsers) -> None:
    from .wiring import SOURCES

    cues = subparsers.add_parser("global-cues", help="US closes, US 10-year, Brent and USD/INR (story A17)")
    cues.add_argument("action", choices=("fill", "check", "verify"))
    cues.add_argument("--cue", action="append", choices=[s.cue for s in SOURCES], help="one cue (repeatable)")
    cues.add_argument("--from", dest="start", type=date.fromisoformat, default=None, help="YYYY-MM-DD")
    cues.add_argument("--to", dest="end", type=date.fromisoformat, default=None, help="YYYY-MM-DD (default: today)")
    cues.set_defaults(func=cmd_global_cues)


def cmd_global_cues(args) -> int:
    return {"fill": _fill, "check": _check, "verify": _verify}[args.action](args)


def _fill(args) -> int:
    from .wiring import build_job, sources_named

    lines, ok = build_job().run(sources_named(args.cue), args.start, args.end or now_ist().date())
    print("\n".join(lines))
    return 0 if ok else 1


def _check(args) -> int:
    from .wiring import build_checks

    print("\n".join(build_checks().write()))
    return 0


def _verify(args) -> int:
    from .wiring import build_tables, build_verifier, sources_named

    verifier, tables = build_verifier(), build_tables()
    problems = [p for s in sources_named(args.cue) for p in verifier.problems(s, tables[s.cue].rows())]
    print("\n".join(problems) or "every cue row equals the archived copy it names")
    return 1 if problems else 0
