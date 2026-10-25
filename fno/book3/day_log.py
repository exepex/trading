"""Book 3's day log (story F6): the answer's reason for the day; every proposal of the day, registered or refused with
its reason; every pick that could not trade (not a built candidate, named twice, refused terms); and every registered
strategy D5 refused today. Canonical JSON, written once per day under `journal/book3_ai/proposals/`, committed with
the day's run (`DecidedRun.files`)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path

from ..constants import BOOK3_AI, JOURNAL_FOLDER
from ..playbook.selection import Attempt
from .json_files import write_new_json

LOG_FOLDER = f"{JOURNAL_FOLDER}/{BOOK3_AI}/proposals"
KIND, SCHEMA_VERSION = "book3_day_log", 1


def log_path(day: date) -> str:
    return f"{LOG_FOLDER}/{day.isoformat()}.json"


def write_day_log(root: Path, day: date, reason: str, proposals: Sequence[Mapping], attempted: Sequence[Attempt],
                  excluded: Mapping[str, str]) -> Path:  # fmt: skip
    """`reason`: the answer's own reason for the day (the D3 day record keeps D2's account of what was chosen)."""
    body = {
        "kind": KIND, "schema_version": SCHEMA_VERSION, "day": day.isoformat(), "reason": reason,
        "proposals": list(proposals),
        "attempted_picks": [{**a.pick.to_json(), "why": a.why} for a in attempted],
        "excluded_strategies": dict(sorted(excluded.items())),
    }  # fmt: skip
    return write_new_json(Path(root) / log_path(day), body)
