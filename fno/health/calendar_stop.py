"""One named line when any command stops on NSE's calendar (story O8c, response 239 item 4). Every job that asks the
calendar about a day it does not cover raises `CalendarError`; most let it escape as a traceback, and their workflows
then blamed Drive or claimed an alert that was never sent. `fno/cli.py` sends that error here once, for every command:
one line to #fno-desk naming the command and the calendar's own words (the day and the year to add), exit 1. A command
that handles the calendar itself (the 3 pm recorder, A16, the back-fill) never lets it reach here, so nothing is posted
twice."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence

CALENDAR_STOP = "Omenix F&O `{command}` stopped: {reason}"


def command_name(argv: Sequence[str] | None) -> str:
    """The command and its action, without options (`pipeline index-closes`, `data-librarian index-close`)."""
    tokens = list(sys.argv[1:] if argv is None else argv)
    words = [token for token in tokens[:2] if not token.startswith("-")]
    return " ".join(words) or "fno"


def calendar_stop(command: str, error: Exception, send: Callable[[str], str] | None = None, out=print) -> int:
    if send is None:
        from ..composition import build_alert_sender

        send = build_alert_sender().send
    line = CALENDAR_STOP.format(command=command, reason=error)
    out(line)
    out(send(line))
    return 1
