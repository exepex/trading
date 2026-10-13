"""The two scheduled filings jobs (story A12): `filings archive` and `filings day-lists`. Each commits the manifest rows
it wrote, finished or stopped, and alerts #fno-desk when something needs the owner (never for the time limit).
"""

from __future__ import annotations

from datetime import date, timedelta

from ..storage.librarian_cli import SIGN_IN_REFUSED, print_now, run_librarian
from ..storage.owner_token import DriveSignInRefused

DEFAULT_MAX_MINUTES = 330  # GitHub stops a job at 6 hours; this leaves time to commit the manifest rows
DAILY_GAP_HOURS = 20  # after a complete run, the next full check waits this long (one check a day)
ALREADY_DONE = "filings archive: complete run at {finished:%Y-%m-%d %H:%M}, less than {hours} h ago; nothing to do"
NEEDS_OWNER = "Omenix F&O filings archive: {problem}. Run log: research/data/manifests/filings/runs.csv"
RUN_LINE = "Omenix F&O filings archive: {done}, {gaps} gaps with reasons; {state}"
SHOWN_LINES = 30  # gap and failure lines printed per run (all of them are in gaps.csv and the alert count)


def add_archive_parsers(actions) -> None:
    from .wiring import BACKFILL_SINCE, DAY_LISTS

    archive = actions.add_parser("archive", help="archive the Nifty 500's results and shareholding XBRL files")
    archive.add_argument("--since", type=date.fromisoformat, default=BACKFILL_SINCE, help="YYYY-MM-DD")
    archive.add_argument("--max-minutes", type=int, default=DEFAULT_MAX_MINUTES, help="stop after this long")
    archive.add_argument("--symbols", help="comma-separated symbols (default: the Nifty 500 list)")
    archive.add_argument("--daily", action="store_true", help=f"skip if a complete run ended < {DAILY_GAP_HOURS} h ago")
    archive.set_defaults(func=cmd_filings_archive)
    lists = actions.add_parser("day-lists", help="archive NSE's all-company announcement and board-meeting lists")
    lists.add_argument("--name", choices=sorted(DAY_LISTS), help="one list (default: both)")
    lists.add_argument("--from", dest="start", type=date.fromisoformat, default=None, help="YYYY-MM-DD")
    lists.add_argument(
        "--to", dest="end", type=date.fromisoformat, default=None, help="YYYY-MM-DD (default: yesterday)"
    )
    lists.set_defaults(func=cmd_filings_day_lists)


def cmd_filings_archive(args) -> int:
    from ..composition import build_alert_sender
    from ..models import now_ist
    from ..storage.wiring import build_manifest_recorder
    from .wiring import build_run_log

    runs, started = build_run_log(), now_ist()
    recorder = build_manifest_recorder()
    try:
        return _archive(args, started, runs, build_alert_sender())
    finally:
        print(recorder.commit("filings archive"))  # manifest rows, gaps and run log, finished or stopped


def _archive(args, started, runs, alerts) -> int:
    from ..models import now_ist
    from .wiring import build_companies, build_filings_librarian, build_gap_log

    deadline = started + timedelta(minutes=args.max_minutes)
    try:
        companies = args.symbols.split(",") if args.symbols else build_companies()
        last = runs.last_complete(len(companies))
        if args.daily and last and started - last < timedelta(hours=DAILY_GAP_HOURS):
            print(ALREADY_DONE.format(finished=last, hours=DAILY_GAP_HOURS))
            return 0
        report = build_filings_librarian(print_now).run(companies, args.since, deadline)
    except DriveSignInRefused as exc:
        message = SIGN_IN_REFUSED.format(reason=exc.reason)
        print(message)
        print(alerts.send(message))
        return 1
    build_gap_log().replace(report.checked, report.gaps)
    runs.append(started, now_ist(), report)
    for line in _report_lines(report):
        print(line)
    problem = _problem(report)
    print(alerts.send(_run_line(report, problem)))  # one line per run that did work; "nothing to do" runs stay quiet
    return 1 if problem else 0


def _run_line(report, problem: str) -> str:
    done = f"{len(report.checked)} of {report.companies} companies checked, {report.saved} files saved"
    if problem:
        return NEEDS_OWNER.format(problem=f"{done}; {problem}")
    state = "complete" if report.complete else "continues in the next run"
    return RUN_LINE.format(done=done, gaps=len(report.gaps), state=state)


def _report_lines(report) -> list[str]:
    lines = [
        f"companies {report.companies}, checked {len(report.checked)}, saved {report.saved}, "
        f"already there {report.present}, gaps {len(report.gaps)}, failures {len(report.failures)}"
    ]
    lines += [f"gap {g.symbol} {g.kind}: {g.reason}" for g in report.gaps[:SHOWN_LINES]]
    lines += [f"FAILED {line}" for line in report.failures[:SHOWN_LINES]]
    lines.append(f"result: {'complete' if report.complete else 'INCOMPLETE: ' + (report.stopped or 'failures above')}")
    return lines


def _problem(report) -> str:
    """What needs the owner; "" when nothing does (a run stopped only by its time limit resumes by itself)."""
    if report.failures:
        return f"{len(report.failures)} list(s) or file(s) failed (first: {report.failures[0]})"
    if report.stopped and not report.stopped.startswith("deadline"):
        return report.stopped
    return ""


def cmd_filings_day_lists(args) -> int:
    from ..composition import build_alert_sender
    from ..storage.wiring import build_manifest_folder, build_manifest_recorder
    from .wiring import DAY_LISTS, build_day_list_librarian

    end = args.end or date.today() - timedelta(days=1)
    worst = 0
    for name in [args.name] if args.name else sorted(DAY_LISTS):
        start = args.start or first_unarchived_day(DAY_LISTS[name], end, build_manifest_folder())
        build = lambda name=name: build_day_list_librarian(name, log=print_now)  # noqa: E731 - one per list
        worst = max(worst, run_librarian(build, build_alert_sender(), build_manifest_recorder(), name, start, end))
    return worst


def first_unarchived_day(source, end: date, manifests) -> date:
    """The first day from the list's first day to `end` without a manifest row, so a daily run reads only what is
    new instead of re-reading three years of files from Drive (`end` + 1 when every day is archived)."""
    archived = {f.day for f in manifests.read(source)}
    day = source.first_day
    while day <= end and day in archived:
        day += timedelta(days=1)
    return day
