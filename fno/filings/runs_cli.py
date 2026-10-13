"""The two scheduled filings jobs (story A12): `filings archive` and `filings day-lists`. Each follows the owner's work
queue in the progress record (Drive), commits the manifest rows it wrote, and posts one line to #fno-desk.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import partial

from ..models import now_ist
from ..storage.librarian_cli import SIGN_IN_REFUSED, print_now, run_librarian
from ..storage.manifest_commit import COMMITTED, NOTHING
from ..storage.owner_token import DriveSignInRefused
from .progress import QUEUE

DEFAULT_MAX_MINUTES = 260  # leaves the 6-hour job time for the day lists and the commits
DEFAULT_DAY_LIST_MINUTES = 50  # with the archive's 260: 310 of the job's 355 minutes, room for setup and commits
DAILY_GAP_HOURS = 20  # after the backfill, one full check a day
ALREADY_DONE = "filings archive: daily check done at {finished:%Y-%m-%d %H:%M}, less than {hours} h ago; nothing to do"
GB = 1e9
SHOWN_LINES = 30  # gap and failure lines printed per run (all gaps are in gaps.csv)
KEPT = (COMMITTED.split("(")[0], NOTHING)  # commit outcomes after which the manifest rows are safe in the repository


def add_archive_parsers(actions) -> None:
    from .wiring import DAY_LISTS

    archive = actions.add_parser("archive", help="results and shareholding XBRL files, following the work queue")
    archive.add_argument("--max-minutes", type=int, default=DEFAULT_MAX_MINUTES, help="stop after this long")
    archive.add_argument("--symbols", help="comma-separated symbols: only these, within the current step")
    archive.set_defaults(func=cmd_filings_archive)
    lists = actions.add_parser("day-lists", help="archive NSE's all-company announcement and board-meeting lists")
    lists.add_argument("--name", choices=sorted(DAY_LISTS), help="one list (default: both)")
    lists.add_argument("--max-minutes", type=int, default=DEFAULT_DAY_LIST_MINUTES, help="stop after this long")
    lists.add_argument(
        "--to", dest="end", type=date.fromisoformat, default=None, help="YYYY-MM-DD (default: yesterday)"
    )
    lists.set_defaults(func=cmd_filings_day_lists)


def cmd_filings_archive(args) -> int:
    from ..composition import build_alert_sender
    from ..storage.wiring import build_manifest_recorder
    from .wiring import build_companies, build_filings_librarian, build_gap_log, build_progress, write_symbol_map

    started, alerts = now_ist(), build_alert_sender()
    try:
        companies, progress = build_companies(), build_progress()
        step = progress.step()
        last = progress.last_daily_run()
        if step is None and last and started - last < timedelta(hours=DAILY_GAP_HOURS):
            print(ALREADY_DONE.format(finished=last, hours=DAILY_GAP_HOURS))
            return 0
        write_symbol_map()
        todo = progress.remaining(step, companies)
        if args.symbols:
            todo = [s for s in todo if s in set(args.symbols.split(","))]
        deadline = started + timedelta(minutes=args.max_minutes)
        report = build_filings_librarian(print_now).run(todo, progress.since(step, started.date()), deadline)
    except DriveSignInRefused as exc:
        message = SIGN_IN_REFUSED.format(reason=exc.reason)
        print(message)
        print(alerts.send(message))
        return 1
    build_gap_log().replace(report.checked, report.gaps)
    committed = build_manifest_recorder().commit("filings archive")
    print(committed)
    if committed.startswith(KEPT):  # a company counts as finished only once its manifest rows are kept
        progress.finish_companies(step, report.finished)
        progress.finish_step_if_done(step, companies)
    progress.record_run(step, started, now_ist(), report)
    totals = archive_totals()
    progress.save(totals)
    for line in report_lines(report):
        print(line)
    problem = problem_of(report, committed)
    print(alerts.send(run_line(step, progress, companies, report, totals, problem)))
    return 1 if problem else 0


def archive_totals() -> dict:
    from ..constants import FILING_FILE_KINDS
    from .wiring import build_filings_manifest

    manifest = build_filings_manifest()
    rows = [r for kind in FILING_FILE_KINDS for r in manifest.rows(kind).values()]
    return {"files": len(rows), "bytes": sum(r.size_bytes for r in rows)}


def report_lines(report) -> list[str]:
    lines = [
        f"companies {report.companies}, checked {len(report.checked)}, saved {report.saved} "
        f"({report.bytes_saved / GB:.2f} GB), already there {report.present}, gaps {len(report.gaps)}, "
        f"failures {len(report.failures)}"
    ]
    lines += [f"gap {g.symbol} {g.kind}: {g.reason}" for g in report.gaps[:SHOWN_LINES]]
    lines += [f"FAILED {line}" for line in report.failures[:SHOWN_LINES]]
    lines.append(f"result: {'complete' if report.complete else 'INCOMPLETE: ' + (report.stopped or 'failures above')}")
    return lines


def problem_of(report, committed: str) -> str:
    """What needs the owner; "" when nothing does (a run stopped only by its time limit resumes by itself)."""
    if not committed.startswith(KEPT):
        return committed
    if report.failures:
        return f"{len(report.failures)} list(s) or file(s) failed (first: {report.failures[0]})"
    if report.stopped and not report.stopped.startswith("deadline"):
        return report.stopped
    return ""


def run_line(step, progress, companies, report, totals: dict, problem: str) -> str:
    """The one line each run posts: where the queue is, this run's files and size, the archive's totals."""
    name = f"step {step.name}" if step else "daily check"
    done = len(companies) - len(progress.remaining(step, companies)) if step else len(report.finished)
    state = problem or ("step finished" if step and step.name in progress.state.get("finished_steps", []) else "")
    return (
        f"Omenix F&O filings archive, {name}: {done} of {len(companies)} companies done; this run "
        f"{report.saved} files, {report.bytes_saved / GB:.2f} GB, {len(report.failures)} failures; archive "
        f"{totals['files']} files, {totals['bytes'] / GB:.2f} GB" + (f"; {state}" if state else "")
    )


def cmd_filings_day_lists(args) -> int:
    from ..composition import build_alert_sender
    from ..storage.wiring import build_manifest_folder, build_manifest_recorder
    from .wiring import DAY_LISTS, build_progress

    step = build_progress().step()
    first = step.day_lists_since if step else QUEUE[-1].day_lists_since
    end = args.end or date.today() - timedelta(days=1)
    deadline = now_ist() + timedelta(minutes=args.max_minutes)
    worst = 0
    for name in [args.name] if args.name else sorted(DAY_LISTS):
        start = first_unarchived_day(DAY_LISTS[name], end, build_manifest_folder(), first)
        build = partial(_budgeted_day_list, name, deadline)
        worst = max(worst, run_librarian(build, build_alert_sender(), build_manifest_recorder(), name, start, end))
    return worst


def _budgeted_day_list(name: str, deadline):
    from .day_lists import TimeBudgetedFill
    from .wiring import build_day_list_librarian

    return TimeBudgetedFill(build_day_list_librarian(name, log=print_now), now_ist, deadline)


def first_unarchived_day(source, end: date, manifests, first: date) -> date:
    """The first day from `first` to `end` without a manifest row, so a run reads only what is new instead of
    re-reading years of files from Drive (`end` + 1 when every day is archived)."""
    archived = {f.day for f in manifests.read(source)}
    day = max(first, source.first_day)
    while day <= end and day in archived:
        day += timedelta(days=1)
    return day
