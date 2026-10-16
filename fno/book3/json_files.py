"""Book 3's write-once JSON files (the day log, the shadow file): canonical bytes, written atomically, never twice."""

from __future__ import annotations

from pathlib import Path

from ..books.files import write_atomic
from ..desk.pack_items import canonical_json


def write_new_json(path: Path, body: dict) -> Path:
    """FileExistsError when the file is already there: each of these files is written once."""
    if path.exists():
        raise FileExistsError(f"{path} is already written: once a day")
    path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(path, path.with_suffix(".tmp"), canonical_json(body).decode("utf-8"))
    return path
