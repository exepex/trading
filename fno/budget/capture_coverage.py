"""Which fired AI book sessions have no usage row yet (story F8 criterion 7). The fire logs keep each routine
session's link (`.../cse_<id>`); the session tools name a session `session_<id>`. Matching is on the part after the
prefix, an assumption (reasoning only: both name the same session in the examples seen) that the judge should test.
Both protocols' fire logs are read (G11: v4's sit in `ai_v4/` with their books under "books", `RunTerms`), so a v4
run that published no timing is named as not captured, as a v2 run is."""

from __future__ import annotations

import json
from pathlib import Path

from ..ai.run_terms import V2_TERMS, V4_TERMS, RunTerms
from .usage_ledger import session_key

FIRE_LOGS = "*/*_fired.json"


class FireLogUnreadable(ValueError):
    """A fire log is not the {book: {fired, session}} object F1 writes; the message names the file."""


def fired_sessions(root: Path, month: str, before: str) -> list[tuple[str, str, str]]:
    """(day, book, session link) of every fired book session in the month's fire logs, on days before `before` (a
    session of today cannot be captured yet: only complete days are recorded)."""
    found = []
    for terms in (V2_TERMS, V4_TERMS):
        for log in sorted((root / terms.folder).glob(FIRE_LOGS)):
            day = log.name.removesuffix("_fired.json")
            if day.startswith(month) and day < before:
                found += [(day, book, session) for book, session in _fired(log, terms)]
    return sorted(found)


def _fired(log: Path, terms: RunTerms) -> list[tuple[str, str]]:
    try:
        entries = terms.fired_books(json.loads(log.read_text(encoding="utf-8")))
        if not isinstance(entries, dict) or not all(isinstance(e, dict) for e in entries.values()):
            raise ValueError
    except ValueError:
        raise FireLogUnreadable(f"{log.name}: not a fire log of book -> entry objects") from None
    # a fired session without a link cannot be captured either, so it counts as missing
    return [(book, e.get("session") or "") for book, e in entries.items() if e.get("fired")]


def not_captured(root: Path, month: str, usage_rows: list[dict], before: str) -> list[tuple[str, str, str]]:
    captured = {session_key(row["session_id"]) for row in usage_rows}
    return [fired for fired in fired_sessions(root, month, before) if session_key(fired[2]) not in captured]
