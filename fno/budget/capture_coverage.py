"""Which fired AI book sessions have no usage row yet (story F8 criterion 7). The fire logs keep each routine
session's link (`.../cse_<id>`); the session tools name a session `session_<id>`. Matching is on the part after the
prefix, an assumption (reasoning only: both name the same session in the examples seen) that the judge should test."""

from __future__ import annotations

import json
from pathlib import Path

from ..ai.paths import AI_FOLDER

FIRE_LOGS = "*/*_fired.json"


def session_key(session: str) -> str:
    """`https://claude.ai/code/cse_01X` and `session_01X` both give `01X`."""
    return session.rstrip("/").rsplit("/", 1)[-1].split("_", 1)[-1]


def fired_sessions(root: Path, month: str) -> list[tuple[str, str, str]]:
    """(day, book, session link) of every fired book session in the month's fire logs."""
    found = []
    for log in sorted((root / AI_FOLDER).glob(FIRE_LOGS)):
        day = log.name.removesuffix("_fired.json")
        if not day.startswith(month):
            continue
        for book, entry in json.loads(log.read_text(encoding="utf-8")).items():
            if entry.get("fired"):  # a fired session without a link cannot be captured either
                found.append((day, book, entry.get("session") or ""))
    return found


def not_captured(root: Path, month: str, usage_rows: list[dict]) -> list[tuple[str, str, str]]:
    captured = {session_key(row["session_id"]) for row in usage_rows}
    return [fired for fired in fired_sessions(root, month) if session_key(fired[2]) not in captured]
