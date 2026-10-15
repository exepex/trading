"""`python -m fno vix-history <fill|sweep|check|verify>` (story A15).

- fill: archives the missing month files from NSE to the owner's Drive (with manifest rows), extends the table from
  them, then writes the checks. Resumable: run it again and only missing months are fetched.
- sweep: reads every month again from NSE and keeps a changed one as an A11 revision, named day by day.
- check: rewrites the checks from the committed table (no network).
- verify: recomputes the table from the month files in Drive and lists every difference (read-only).
Commit `research/data/vix/` and `research/data/manifests/` after a run: rows are evidence only once committed.
"""

from __future__ import annotations

from datetime import date, datetime

from ..models import now_ist
from ..storage.raw_source import RawSourceUnavailable
from .source import NseVixHistorySource, last_complete_month, months_between
from .table import VixTableConflict

MONTH_FORMAT = "%Y-%m"
COMMIT_REMINDER = "commit research/data/vix/ and research/data/manifests/ (rows are evidence only once committed)"


def _month(text: str) -> date:
    return datetime.strptime(text, MONTH_FORMAT).date()


def add_vix_history_parser(subparsers) -> None:
    vix = subparsers.add_parser("vix-history", help="India VIX daily history from NSE (story A15)")
    vix.add_argument("action", choices=("fill", "sweep", "check", "verify"))
    vix.add_argument("--from", dest="start", type=_month, default=None, help="YYYY-MM (default: NSE's first month)")
    vix.add_argument("--to", dest="end", type=_month, default=None, help="YYYY-MM (default: the last ended month)")
    vix.set_defaults(func=cmd_vix_history)


def cmd_vix_history(args) -> int:
    return {"fill": _fill, "sweep": _sweep, "check": _check, "verify": _verify}[args.action](args)


def _months(args) -> list[date]:
    last_ended = last_complete_month(now_ist().date())
    end = min(args.end or last_ended, last_ended)  # a month still running is never fetched: its file would grow
    return months_between(args.start or NseVixHistorySource.first_day, end)


def _fill(args) -> int:
    from .wiring import build_vix_librarian, build_vix_raw_area, build_vix_table, build_vix_table_builder

    raw, months = build_vix_raw_area(), _months(args)
    try:
        report = build_vix_librarian(raw).fill(months)
    except RawSourceUnavailable as exc:
        print(f"stopped: {exc}. Run the same command again later (only missing months are fetched).")
        return 1
    print("\n".join(report.lines()))
    every_month = months_between(NseVixHistorySource.first_day, months[-1]) if months else []
    try:
        extension = build_vix_table_builder(raw).extend(every_month)
    except VixTableConflict as exc:
        print(f"table REFUSED (nothing rewritten): {exc}")
        return 1
    print("\n".join(extension.lines(build_vix_table())))
    _check(args)
    print(COMMIT_REMINDER)
    return 0 if report.complete and not extension.stopped_at else 1


def _sweep(args) -> int:
    from .wiring import build_vix_revision_sweep

    report = build_vix_revision_sweep().sweep(_months(args))
    print("\n".join(report.lines()))
    print(COMMIT_REMINDER)
    return 0 if not (report.unanswered or report.invalid) else 1


def _check(args) -> int:
    from .wiring import build_vix_checks, build_vix_table

    print("\n".join(build_vix_checks().write(build_vix_table().rows())))
    return 0


def _verify(args) -> int:
    from .wiring import build_vix_raw_area, build_vix_table, build_vix_verifier

    rows = build_vix_table().rows()
    problems = build_vix_verifier(build_vix_raw_area()).problems(rows)
    print("\n".join(problems) or f"India VIX table: all {len(rows)} days equal their archived month files")
    return 1 if problems else 0
