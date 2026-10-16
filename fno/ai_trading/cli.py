"""`python -m fno ai-trading <action>`: the transcript audit of the AI books' decision sessions (story F1t), by the
forecasts' rule and with their code: every session of the first 10 fired days, then 2 a week drawn with the verified
weekly seed; a breach makes that book-day unscored, and two in 20 decision days stop that book's decision fires.

- `audits-due`: records any new weekly draw of decision sessions, then lists the selected sessions not audited yet;
- `audit-record`: records one decision session's transcript audit (clean, or the breach kinds found), written once.
"""

from __future__ import annotations

import json
from datetime import date

from ..ai.fire_once import FIRE_UNKNOWN
from ..ai.transcript_audit import BREACH_KINDS
from ..constants import AI_BOOKS

DRAWS_FOLDER = "journal/ai_decisions/draws"


def add_ai_trading_parser(subparsers) -> None:
    parser = subparsers.add_parser("ai-trading", help="the AI books' decision sessions: transcript audits (F1t)")
    actions = parser.add_subparsers(dest="ai_trading_cmd", required=True)
    actions.add_parser("audits-due", help="decision sessions selected for a transcript audit and not yet audited")
    record = actions.add_parser("audit-record", help="record one decision session's transcript audit (written once)")
    record.add_argument("--day", type=date.fromisoformat, required=True, help="YYYY-MM-DD")
    record.add_argument("--book", required=True, choices=AI_BOOKS)
    record.add_argument("--breach", action="append", default=[], choices=BREACH_KINDS, help="a breach kind found")
    record.add_argument("--evidence", required=True, help="what was read and seen (tool calls, files), never a secret")
    record.add_argument("--auditor", required=True, help="who read the transcript")
    record.add_argument("--session", default="", help="the session, when the fire log has no link")
    parser.set_defaults(func=cmd_ai_trading)


def cmd_ai_trading(args) -> int:
    return _audit_record(args) if args.ai_trading_cmd == "audit-record" else _audits_due()


def _audits_due() -> int:
    from ..ai.audit_plan import audits_due, record_draws
    from ..ai.transcript_audit import TranscriptAudits
    from ..ai.wiring import build_audit_seeds
    from ..composition import build_alert_sender
    from ..config import ROOT
    from .paths import DECISIONS_FOLDER, transcript_audit_path

    seeds, refused = build_audit_seeds(ROOT, folder=DECISIONS_FOLDER)
    for line in refused:  # a close the archive does not confirm: that week is not drawn, and the desk is told
        print(line, "|", build_alert_sender().send(line))
    drawn = record_draws(ROOT, seeds, DECISIONS_FOLDER, DRAWS_FOLDER)
    due = audits_due(ROOT, seeds, DECISIONS_FOLDER, TranscriptAudits(ROOT, transcript_audit_path))
    print(
        f"Omenix F&O AI decision transcript audits due: {len(due)}"
        + (f"; new weekly draws: {', '.join(drawn)}" if drawn else "")
    )
    for session in due:
        print(f"  {session.day} {session.book} {session.entry.get('session', '(no link)')}")
    return 0


def _audit_record(args) -> int:
    from ..ai.transcript_audit import AuditRefused, TranscriptAudits, new_audit
    from ..config import ROOT
    from ..models import now_ist
    from .paths import fired_path, transcript_audit_path

    log = ROOT / fired_path(args.day)
    fired = json.loads(log.read_text(encoding="utf-8")).get(args.book, {}) if log.is_file() else {}
    if fired.get("state") == FIRE_UNKNOWN and args.session:  # it may have run: its transcript is auditable by link
        fired = fired | {"fired": True}
    try:
        audit = new_audit(args.day, args.book, fired, args.breach, args.evidence, args.auditor, now_ist(), args.session)
        print(f"recorded {audit.result}: {TranscriptAudits(ROOT, transcript_audit_path).record(args.day, audit)}")
    except AuditRefused as refused:
        print(f"refused: {refused}")
        return 1
    return 0
