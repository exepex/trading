"""`python -m fno rates capture | show` (story A21). Research data only: reads RBI's public pages, never trades."""

from __future__ import annotations

import argparse
from datetime import datetime

from ..alerts.sender import NOT_SENT
from .constants import RATES

ALERT_NOT_SENT = NOT_SENT.split(":")[0]
EXIT_NOT_ALERTED = 1


def add_rates_parser(subparsers) -> None:
    rates = subparsers.add_parser("rates", help="RBI's T-bill cut-off yields and policy repo rate (story A21)")
    actions = rates.add_subparsers(dest="rates_cmd", required=True)
    capture = actions.add_parser("capture", help="read RBI's pages, store them in Drive, add new rows, check, alert")
    capture.add_argument("--dry-run", action="store_true", help="a local folder for Drive; nothing posted or committed")
    show = actions.add_parser("show", help="each rate as known at a moment (default: now)")
    show.add_argument(
        "--as-of", type=_aware, default=None, help="ISO time with its offset, e.g. 2026-10-16T14:30+05:30"
    )
    rates.set_defaults(func=cmd_rates)


def _aware(text: str) -> datetime:
    moment = datetime.fromisoformat(text)
    if moment.tzinfo is None:
        raise argparse.ArgumentTypeError(f"{text!r} has no offset: write e.g. {text}+05:30")
    return moment


def cmd_rates(args) -> int:
    return _capture(args.dry_run) if args.rates_cmd == "capture" else _show(args.as_of)


def _capture(dry_run: bool) -> int:
    from .wiring import build_rates_capture

    result = build_rates_capture(dry_run).run()
    for row in result.added:
        print(f"added: {row.rate} {row.value_pct}% ({row.value_date}, first seen {row.first_seen_at})")
    for step, kind, message in result.problems:
        print(f"problem [{kind}] at {step}: {message}")
    for note in result.notes:
        print(note)
    if result.alert:
        print(f"alert: {result.alert}")
    # its own O10 rows and alert are the record; exit 1 only when the alert did not go out (capture-watch then posts).
    # The workflow commits the receipts and the O10 rows together in one step; a failed push fails the run.
    return EXIT_NOT_ALERTED if not dry_run and result.alert.startswith(ALERT_NOT_SENT) else 0


def _show(as_of: datetime | None) -> int:
    from ..models import IST
    from .wiring import build_rates_as_of

    cutoff, rates = as_of or datetime.now(IST), build_rates_as_of()
    for rate in RATES:
        row = rates.value(rate, cutoff)
        known = f"{row.value_pct}% ({row.value_date}, first seen {row.first_seen_at})" if row else "no rate"
        print(f"{rate}: {known}")
    return 0
