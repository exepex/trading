"""`python -m fno lab close [--day D]` (story FL1-1): the 15:45 report to #fno-forecast, run by O1's `lab_close` step.
Exit 0 when the report was posted or there was nothing to post (not a regular session, an already-posted rerun); exit
1 when it was not posted, so O1's `Alerted` alerts the failure once (the command never alerts its own failure).
`python -m fno lab channels`: criterion 7's read-only membership check of the lab's two channels, a go-live check;
exit 1 unless the bot is a member of both."""

from __future__ import annotations

import os
from datetime import date

NO_TOKEN = "lab channels: FNO_SLACK_BOT_TOKEN is not set; membership not checked"


def add_lab_parser(subparsers) -> None:
    p = subparsers.add_parser("lab", help="FL1: the forecast lab's 15:45 report; its channels' membership check")
    p.add_argument("action", choices=("close", "channels"))
    p.add_argument("--day", type=date.fromisoformat, default=None)
    p.set_defaults(func=cmd_lab)


def cmd_lab(args, out=print, env=os.environ) -> int:
    return _channels(out, env) if args.action == "channels" else _close(args.day, out)


def _close(day: date | None, out) -> int:
    from ..models import now_ist
    from .wiring import build_lab_close

    result = build_lab_close().run(day or now_ist().date())
    for line in result.lines:
        out(line)
    return 1 if result.failed else 0


def _channels(out, env) -> int:
    import requests

    from ..constants import ENV_FNO_SLACK_BOT_TOKEN
    from .membership import check_membership

    token = env.get(ENV_FNO_SLACK_BOT_TOKEN)
    if not token:
        out(NO_TOKEN)
        return 1
    lines, every = check_membership(requests.Session(), token)
    for line in lines:
        out(line)
    return 0 if every else 1
