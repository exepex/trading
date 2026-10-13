"""Which routine sessions must be audited (owner's condition 1, 14 Oct 2026): every session of the first 10 session days
on which the AI books were fired, then 2 sessions a week drawn at random from that week's fired sessions. The draw is
fixed by the week (a seed from its ISO year and number) and made only once the week is over, so it cannot be steered
by what the sessions turned out to contain, and anyone can redraw it."""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .paths import AI_FOLDER
from .transcript_audit import TranscriptAudits

FIRST_DAYS_ALL_AUDITED = 10
WEEKLY_SAMPLE = 2
FIRED_SUFFIX = "_fired.json"


@dataclass(frozen=True, order=True)
class FiredSession:
    day: date
    book: str
    entry: dict  # the fire log's entry: version, session link, time


def fired_sessions(root: Path) -> list[FiredSession]:
    """Every book-day that was actually fired, oldest first."""
    found = []
    for path in sorted((Path(root) / AI_FOLDER).glob(f"*/*{FIRED_SUFFIX}")):
        day = date.fromisoformat(path.name.removesuffix(FIRED_SUFFIX))
        for book, entry in sorted(json.loads(path.read_text(encoding="utf-8")).items()):
            if entry.get("fired"):
                found.append(FiredSession(day, book, entry))
    return found


def sessions_to_audit(sessions: list[FiredSession], today: date) -> list[FiredSession]:
    """The sessions the rule selects, audited or not."""
    days = sorted({s.day for s in sessions})
    first = set(days[:FIRST_DAYS_ALL_AUDITED])
    chosen = [s for s in sessions if s.day in first]
    weeks: dict[tuple[int, int], list[FiredSession]] = {}
    for s in sessions:
        if s.day not in first:
            weeks.setdefault(s.day.isocalendar()[:2], []).append(s)
    for week, members in sorted(weeks.items()):
        if week < today.isocalendar()[:2]:  # only a finished week is drawn
            seed = int(hashlib.sha256(f"{week[0]}-W{week[1]:02d}".encode()).hexdigest(), 16)
            chosen += random.Random(seed).sample(sorted(members), min(WEEKLY_SAMPLE, len(members)))
    return sorted(chosen)


def audits_due(root: Path, today: date) -> list[FiredSession]:
    """Selected sessions without an audit record yet."""
    audits = TranscriptAudits(root)
    return [s for s in sessions_to_audit(fired_sessions(root), today) if audits.get(s.day, s.book) is None]
