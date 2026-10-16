"""The stop rule (owner's condition 1, 14 Oct 2026): two transcript breaches by one book within its last 20 session days
stop that book's fires until the prompt or design is fixed, which means a new registered version (breaches of an
older version do not count against the new one). The fire step asks this before each book."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from pathlib import Path

from .coverage import pack_days
from .transcript_audit import BREACH, TranscriptAudits

WINDOW_SESSION_DAYS, BREACHES_TO_STOP = 20, 2
STOPPED = "stopped: {count} transcript breaches in {window} session days ({days}); register a fixed version"


def breached_days(root: Path, book: str, version: str, before: date, days: Sequence[date] | None = None,
                  audits: TranscriptAudits | None = None) -> list[date]:  # fmt: skip
    """Days among the book's last 20 session days before `before` whose audit, under `version`, found a breach. The
    forecast's pack days and audits by default; story F1t's decision sessions pass their own fired days and audits."""
    window = [d for d in (pack_days(root) if days is None else days) if d < before][-WINDOW_SESSION_DAYS:]
    audits = audits or TranscriptAudits(root)
    return [d for d in window if (a := audits.get(d, book)) and a.result == BREACH and a.version == version]


def stop_reason(root: Path, book: str, version: str, day: date, days: Sequence[date] | None = None,
                audits: TranscriptAudits | None = None) -> str:  # fmt: skip
    """Why the book must not be fired on `day`, or '' when it may."""
    days = breached_days(root, book, version, day, days, audits)
    if len(days) < BREACHES_TO_STOP:
        return ""
    listed = ", ".join(d.isoformat() for d in days)
    return STOPPED.format(count=len(days), window=WINDOW_SESSION_DAYS, days=listed)
