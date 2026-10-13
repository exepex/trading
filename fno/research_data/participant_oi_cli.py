"""Commands for participant open interest (story A8): `python -m fno participant-oi watch` (the release-time recorder)
and `python -m fno participant-oi rule` (the availability rule in force and its evidence)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from ..constants import RELEASE_REWRITTEN, RELEASE_UNREACHABLE
from ..models import IST, now_ist

DEFAULT_UNTIL, DEFAULT_EVERY_MINUTES = time(22, 0), 5
MOVED = "MOVED {day}: NSE rewrote the file at {newer:%Y-%m-%d %H:%M %Z} (recorded {recorded:%Y-%m-%d %H:%M %Z})"


def add_participant_oi_parser(subparsers) -> None:
    oi = subparsers.add_parser("participant-oi", help="NSE participant open interest: release times and the rule")
    actions = oi.add_subparsers(dest="oi_cmd", required=True)
    watch = actions.add_parser("watch", help="check NSE's archive until the day's file appears; log every check")
    watch.add_argument("--day", type=date.fromisoformat, help="YYYY-MM-DD (default: today, IST)")
    watch.add_argument("--until", type=time.fromisoformat, default=DEFAULT_UNTIL, help="HH:MM IST (default 22:00)")
    watch.add_argument("--every", type=int, default=DEFAULT_EVERY_MINUTES, help="minutes between checks (default 5)")
    actions.add_parser("rule", help="print the availability rule in force and how many days are measured")
    actions.add_parser("sweep", help="read every recorded file: flag moved write times, keep new versions (A11)")
    oi.set_defaults(func=cmd_participant_oi)


def cmd_participant_oi(args) -> int:
    from ..composition import build_participant_oi_rule, build_release_time_recorder

    if args.oi_cmd == "sweep":
        return _sweep()
    from ..storage.wiring import PARTICIPANT_OI_RELEASE_LOG
    from .release_times import MIN_MEASURED_DAYS, ReleaseLog, first_seen_times

    if args.oi_cmd == "rule":
        measured = len(first_seen_times(ReleaseLog(PARTICIPANT_OI_RELEASE_LOG).checks()))
        print(f"rule: {build_participant_oi_rule().describe()}; measured days: {measured} of {MIN_MEASURED_DAYS}")
        return 0
    day = args.day or now_ist().date()
    until = datetime.combine(day, args.until, IST)
    recorder = build_release_time_recorder()
    rewritten = [c for c in recorder.recheck_recent(day) if c.outcome == RELEASE_REWRITTEN]
    for c in rewritten:
        print(f"REWRITTEN {c.day}: NSE's file changed after it was first seen (now {c.sha256[:12]})")
    check = recorder.watch(day, until, timedelta(minutes=args.every))
    if check is None:
        print(f"{day}: not a trading day; nothing checked")
    else:
        print(f"{day}: {check.outcome} at {check.checked_at:%Y-%m-%d %H:%M} IST {check.sha256[:12]}".rstrip())
    return 1 if rewritten or (check is not None and check.outcome == RELEASE_UNREACHABLE) else 0


def _sweep() -> int:
    from ..composition import build_last_write_sweep, participant_oi_last_writes
    from ..storage.revisions_cli import revision_lines
    from ..storage.wiring import build_manifest_recorder, build_revision_archive

    archive, recorder = build_revision_archive(), build_manifest_recorder()
    try:
        result = build_last_write_sweep(archive).run(participant_oi_last_writes())
        for day, recorded, newer in result.moved:
            print(MOVED.format(day=day, newer=newer, recorded=recorded))
        for day in result.unanswered:
            print(f"no answer {day}: unreachable or no Last-Modified; check again next sweep")
        print("\n".join(revision_lines(archive)))
        moved, unanswered = len(result.moved), len(result.unanswered)
        print(
            f"sweep: {result.checked} files checked, {moved} moved, {unanswered} unanswered, "
            f"{len(archive.stored)} new revisions"
        )
    finally:
        print(recorder.commit("participant-oi sweep"))  # the revision index rows
    return 1 if result.moved or result.unanswered or archive.stored else 0
