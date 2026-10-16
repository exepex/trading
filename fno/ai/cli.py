"""`python -m fno ai <action>`: the GitHub Actions side of the AI books' forecasts (stories F1 and G5). Research only.

- `fire`: after the day's v2 pack is committed, fires each AI book's routine once (one #fno-desk line per failure);
- `reveals-ready`: exit 0 once every fired book's reveal is in the checkout (or nothing was fired);
- `collect`: after 15:15 IST, turns the books' sealed submissions into records and audit files (written once), then
  records every book run's own timing in BG1's usage ledger and alerts each run of the day not captured (F8c);
- `coverage`: per book, the pack days with a counted forecast (story G5 criterion 3);
- `audits-due`: records any new weekly draw (with its seed inputs), then lists the selected sessions not audited yet;
- `audit-record`: records one session's transcript audit (clean, or the breach kinds found), written once.
The routine side is `python -m fno.ai` (standard library only).
"""

from __future__ import annotations

import json
from datetime import date

from ..constants import AI_BOOKS
from .transcript_audit import BREACH_KINDS


def add_ai_parser(subparsers) -> None:
    ai = subparsers.add_parser("ai", help="the AI books' daily forecasts: fire, collect, coverage (F1, G5)")
    actions = ai.add_subparsers(dest="ai_cmd", required=True)
    for name, text in (("fire", "fire each AI book's routine once for the day"),
                       ("reveals-ready", "exit 0 once every fired book's reveal is in"),
                       ("collect", "record the AI books' forecasts for the day (after 15:15 IST)")):  # fmt: skip
        action = actions.add_parser(name, help=text)
        action.add_argument("--day", type=date.fromisoformat, help="YYYY-MM-DD (default: today in IST)")
    actions.add_parser("coverage", help="pack days with a counted forecast, per AI book")
    actions.add_parser("audits-due", help="routine sessions selected for a transcript audit and not yet audited")
    record = actions.add_parser("audit-record", help="record one routine session's transcript audit (written once)")
    record.add_argument("--day", type=date.fromisoformat, required=True, help="YYYY-MM-DD")
    record.add_argument("--book", required=True, choices=AI_BOOKS)
    record.add_argument("--breach", action="append", default=[], choices=BREACH_KINDS, help="a breach kind found")
    record.add_argument("--evidence", required=True, help="what was read and seen (tool calls, files), never a secret")
    record.add_argument("--auditor", required=True, help="who read the transcript")
    record.add_argument("--session", default="", help="the session, when the fire log has no link")
    ai.set_defaults(func=cmd_ai)


def cmd_ai(args) -> int:
    from ..models import now_ist

    day = getattr(args, "day", None) or now_ist().date()
    if args.ai_cmd == "audit-record":
        return _audit_record(args)
    commands = {"fire": _fire, "reveals-ready": _reveals_ready, "collect": _collect, "coverage": _coverage,
                "audits-due": _audits_due}  # fmt: skip
    return commands[args.ai_cmd](day)


def _fire(day: date) -> int:
    from .wiring import build_ai_firer

    print("\n".join(build_ai_firer().fire(day)))
    return 0


def _reveals_ready(day: date) -> int:
    from ..config import ROOT
    from .paths import fired_path, reveal_path

    log = ROOT / fired_path(day)
    fired = [b for b, e in json.loads(log.read_text(encoding="utf-8")).items() if e["fired"]] if log.is_file() else []
    return 0 if all((ROOT / reveal_path(day, book)).is_file() for book in fired) else 1


def _collect(day: date) -> int:
    from .wiring import build_ai_collector, record_book_usage

    print("\n".join(build_ai_collector().collect(day) + record_book_usage(day)))
    return 0


def _coverage(day: date) -> int:
    from ..config import ROOT
    from .coverage import coverage_lines

    print("\n".join(coverage_lines(ROOT)))
    return 0


def _audits_due(day: date) -> int:
    from ..composition import build_alert_sender
    from ..config import ROOT
    from .audit_plan import audits_due, record_draws
    from .wiring import build_audit_seeds

    seeds, refused = build_audit_seeds()
    for line in refused:  # a close the archive does not confirm: that week is not drawn, and the desk is told
        print(line, "|", build_alert_sender().send(line))
    drawn = record_draws(ROOT, seeds)
    due = audits_due(ROOT, seeds)
    print(
        f"Omenix F&O AI transcript audits due: {len(due)}"
        + (f"; new weekly draws: {', '.join(drawn)}" if drawn else "")
    )
    for session in due:
        print(f"  {session.day} {session.book} {session.entry.get('session', '(no link)')}")
    return 0


def _audit_record(args) -> int:
    from ..config import ROOT
    from ..models import now_ist
    from .paths import fired_path
    from .transcript_audit import AuditRefused, TranscriptAudits, new_audit

    log = ROOT / fired_path(args.day)
    fired = json.loads(log.read_text(encoding="utf-8")).get(args.book, {}) if log.is_file() else {}
    try:
        audit = new_audit(args.day, args.book, fired, args.breach, args.evidence, args.auditor, now_ist(), args.session)
        print(f"recorded {audit.result}: {TranscriptAudits(ROOT).record(args.day, audit)}")
    except AuditRefused as refused:
        print(f"refused: {refused}")
        return 1
    return 0
