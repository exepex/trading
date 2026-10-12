"""Commands for participant open interest (story A8): `python -m fno participant-oi watch` (the release-time recorder)
and `python -m fno participant-oi rule` (the availability rule in force and its evidence)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from ..constants import RELEASE_UNREACHABLE
from ..models import IST, now_ist

DEFAULT_UNTIL, DEFAULT_EVERY_MINUTES = time(22, 0), 5


def add_participant_oi_parser(subparsers) -> None:
    oi = subparsers.add_parser("participant-oi", help="NSE participant open interest: release times and the rule")
    actions = oi.add_subparsers(dest="oi_cmd", required=True)
    watch = actions.add_parser("watch", help="check NSE's archive until the day's file appears; log every check")
    watch.add_argument("--day", type=date.fromisoformat, help="YYYY-MM-DD (default: today, IST)")
    watch.add_argument("--until", type=time.fromisoformat, default=DEFAULT_UNTIL, help="HH:MM IST (default 22:00)")
    watch.add_argument("--every", type=int, default=DEFAULT_EVERY_MINUTES, help="minutes between checks (default 5)")
    actions.add_parser("rule", help="print the availability rule in force and how many days are measured")
    oi.set_defaults(func=cmd_participant_oi)


def cmd_participant_oi(args) -> int:
    from ..composition import build_participant_oi_rule, build_release_time_recorder
    from ..storage.wiring import PARTICIPANT_OI_RELEASE_LOG
    from .release_times import MIN_MEASURED_DAYS, ReleaseLog, first_seen_times

    if args.oi_cmd == "rule":
        measured = len(first_seen_times(ReleaseLog(PARTICIPANT_OI_RELEASE_LOG).checks()))
        print(f"rule: {build_participant_oi_rule().describe()}; measured days: {measured} of {MIN_MEASURED_DAYS}")
        return 0
    day = args.day or now_ist().date()
    until = datetime.combine(day, args.until, IST)
    check = build_release_time_recorder().watch(day, until, timedelta(minutes=args.every))
    if check is None:
        print(f"{day}: not a trading day; nothing checked")
        return 0
    print(f"{day}: {check.outcome} at {check.checked_at:%Y-%m-%d %H:%M} IST {check.sha256[:12]}".rstrip())
    return 1 if check.outcome == RELEASE_UNREACHABLE else 0
