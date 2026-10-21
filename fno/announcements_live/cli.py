"""`python -m fno announcements poll-once | coverage | show` (story A21 part 2). The live polls run inside A16's
recorder routine; these commands are for a one-off check, the day's coverage and what F2 would have read."""

from __future__ import annotations

import argparse
from datetime import date, datetime, time


def _aware(text: str) -> datetime:
    moment = datetime.fromisoformat(text)
    if moment.tzinfo is None:
        raise argparse.ArgumentTypeError(f"{text!r} has no offset: write e.g. {text}+05:30")
    return moment


def add_announcements_parser(subparsers) -> None:
    parser = subparsers.add_parser("announcements", help="NSE announcements first seen during the session (A21)")
    actions = parser.add_subparsers(dest="announcements_cmd", required=True)
    poll = actions.add_parser("poll-once", help="one poll now, as if at an A16 mark")
    poll.add_argument("--dry-run", action="store_true", help="a local folder for Drive; nothing posted or committed")
    poll.add_argument("--mark", type=time.fromisoformat, default=None, help="the A16 mark it stands for (default now)")
    cover = actions.add_parser("coverage", help="the day's 20 window marks: polled ok, failed or no poll")
    cover.add_argument("--day", type=date.fromisoformat, default=None)
    cover.add_argument("--dry-run", action="store_true")
    show = actions.add_parser("show", help="the items known at a cutoff (by first-seen time)")
    show.add_argument("--cutoff", type=_aware, required=True, help="ISO time with offset, e.g. 2026-10-16T14:30+05:30")
    show.add_argument("--dry-run", action="store_true")
    parser.set_defaults(func=cmd_announcements)


def cmd_announcements(args) -> int:
    from ..models import IST
    from .reading import coverage, items_as_of
    from .wiring import build_announcements_poller, day_state

    if args.announcements_cmd == "poll-once":
        now = datetime.now(IST)
        mark = datetime.combine(now.date(), args.mark, IST) if args.mark else now
        build_announcements_poller(args.dry_run).after_mark(now.date(), mark, None, "poll-once")
        args.day = now.date()
    if args.announcements_cmd in ("poll-once", "coverage"):
        day = args.day or datetime.now(IST).date()
        state = day_state(day, args.dry_run)
        print(f"{day}: {len(state.items)} items recorded")
        for mark, what in coverage(day, state.polls):
            print(f"{mark} {what}")
        return 0
    state = day_state(args.cutoff.date(), args.dry_run)
    for row in items_as_of(state.items, args.cutoff):
        print(f"{row['first_seen_at']} {row['symbol']}: {row['desc']} (NSE {row['exchdisstime']})")
    return 0
