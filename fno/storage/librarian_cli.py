"""`python -m fno data-librarian <dataset>`: fills a dataset's gaps in the owner's Google Drive from NSE (story A9).

Resumable: run it again after a stop and it fetches only what is still missing. A refused Drive sign-in stops the
run with a clear error and an alert to #fno-desk naming the owner's fix; nothing is skipped silently.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import partial

from ..alerts.sender import AlertSender
from .owner_token import DriveSignInRefused
from .raw_source import RawSourceUnavailable

SIGN_IN_REFUSED = (
    "Omenix F&O: Google refused the Drive upload sign-in ({reason}), so the data librarian uploaded nothing more. "
    "The owner's consent has expired or was revoked. One-minute fix on your computer: "
    "python3 tools/gdrive_oauth_setup.py <client_secret JSON>, then put the new FNO_GDRIVE_OAUTH_REFRESH_TOKEN in the "
    "cloud environment's settings. To stop it expiring every 7 days, publish the OAuth app "
    "(Google Cloud console, OAuth consent screen, Publish app)."
)
SOURCE_STOPPED = "stopped: {error}. Run the same command again later to resume (only missing files are fetched)."


def add_librarian_parser(subparsers) -> None:
    from .wiring import LIBRARIAN_DATASETS

    lib = subparsers.add_parser("data-librarian", help="upload a dataset's missing raw files to Drive (story A9)")
    lib.add_argument("dataset", choices=sorted(LIBRARIAN_DATASETS))
    lib.add_argument(
        "--from",
        dest="start",
        type=date.fromisoformat,
        default=None,
        help="YYYY-MM-DD (default: the dataset's first day)",
    )
    lib.add_argument(
        "--to",
        dest="end",
        type=date.fromisoformat,
        default=date.today() - timedelta(days=1),
        help="YYYY-MM-DD (default: yesterday)",
    )
    lib.set_defaults(func=cmd_data_librarian)


def cmd_data_librarian(args) -> int:
    from ..composition import build_alert_sender
    from .wiring import build_librarian

    build = partial(build_librarian, args.dataset, log=print_now)
    return run_librarian(build, build_alert_sender(), args.start, args.end)


def print_now(line: str) -> None:
    """Progress shows at once even when the output goes to a log file (a run takes about an hour)."""
    print(line, flush=True)


def run_librarian(build, alerts: AlertSender, start: date, end: date, out=print) -> int:
    from .librarian import fill_report_lines

    try:
        report = build().fill(start, end)
    except DriveSignInRefused as exc:
        message = SIGN_IN_REFUSED.format(reason=exc.reason)
        out(message)
        out(alerts.send(message))
        return 1
    except RawSourceUnavailable as exc:
        out(SOURCE_STOPPED.format(error=exc))
        return 1
    out("\n".join(fill_report_lines(report)))
    return 0 if report.complete else 1
