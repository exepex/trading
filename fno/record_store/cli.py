"""`python -m fno records ...` (story DR1):

- `certify <dataset> [--day D] [--level provisional|certified] [--commit]`: checks every version of the session and
  writes the record (local unless `--commit`, which pushes `receipts/records/` to main). Exit 1 when not recorded.
- `read <dataset> [--day D] [--level ...]`: prints the as-seen pointer of what a reader would get (never a value).
  Exit 1 when no record serves the need."""

from __future__ import annotations

from .constants import ALERT, LEVELS, PROVISIONAL, SEEN_LINE


def add_records_parser(subparsers) -> None:
    from .wiring import DATASETS

    records = subparsers.add_parser("records", help="staging, certification and the as-seen record (DR1)")
    actions = records.add_subparsers(dest="records_action", required=True)
    for name, func, text in (("certify", cmd_certify, "certify a session"), ("read", cmd_read, "read a record")):
        action = actions.add_parser(name, help=text)
        action.add_argument("dataset", choices=DATASETS)
        action.add_argument("--day", help="the session, YYYY-MM-DD (default: today, IST)")
        action.add_argument("--level", choices=LEVELS, default=PROVISIONAL)
        if name == "certify":
            action.add_argument("--commit", action="store_true", help="commit and push the record to main")
        action.set_defaults(func=func)


def _session(args) -> str:
    from ..models import now_ist

    return args.day or now_ist().date().isoformat()


def cmd_certify(args, out=print, certifier=None, alerts=None) -> int:
    """A record not on origin's main, or a conflict, also goes to #fno-desk (an unsent alert is printed in full)."""
    from ..alerts.output import announce
    from .wiring import build_alerts, build_certifier

    certifier = certifier or build_certifier(args.dataset, args.commit)
    outcome = certifier.certify(_session(args), args.level)
    out(outcome.line)
    if outcome.alert:
        announce(alerts or build_alerts(), ALERT.format(line=outcome.line))
    return 0 if outcome.recorded else 1


def cmd_read(args, out=print, reader=None) -> int:
    from .reader import NotRecorded
    from .wiring import build_record_reader

    reader = reader or build_record_reader()
    try:
        seen = reader.read(args.dataset, _session(args), args.level).as_seen
    except NotRecorded as refusal:
        out(str(refusal))
        return 1
    out(SEEN_LINE.format(dataset=seen.dataset, session=seen.session, level=seen.level, path=seen.path,
                         sha=seen.sha256[:12]))  # fmt: skip
    return 0
