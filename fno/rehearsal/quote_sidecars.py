"""When each of Groww's raw 3 pm quote files entered the real record (story REH1p): A4b keeps the file in Drive's raw
area only, with no O9 receipt and no manifest row; what vouches for it is its sidecar in `research/data/quotes`
(`csv_sha256`, `finished_at`), committed to `main`. A rehearsal sees the file once the replay clock has reached both
the attempt's `finished_at` and the committer time of the first commit on the record's `main` (first-parent) that
added the sidecar: the later of the two, so neither an early finish nor a late commit lets it be seen before the record
held it. A sidecar saying the save failed (`raw_file_saved` false), or one not on `main`, never counts.

The sidecars' commits are read once per record checkout and process (one `git log` over the quotes folder)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from ..quotes.drive_only_store import QUOTE_FILE, SIDECAR
from ..quotes.recorder import RAW_FILE_SAVED
from .manifest_rows import RAW_AREA, RECORD_MAIN

QUOTES = Path("research/data/quotes")  # the record's sidecars (`storage.wiring.QUOTES_FOLDER`)


class QuoteSidecars:
    def __init__(self, record: Path):
        self.record = Path(record)

    def seen_at(self, path: str) -> datetime | None:
        """When the record held this raw quote file, or None when no committed sidecar on main vouches for it."""
        if not (path.startswith(RAW_AREA) and path.endswith(QUOTE_FILE)):
            return None
        sidecar = (QUOTES / path.removeprefix(RAW_AREA).removesuffix(QUOTE_FILE)).as_posix() + SIDECAR
        committed = _added(self.record).get(sidecar)
        if committed is None:
            return None
        meta = json.loads((self.record / sidecar).read_text(encoding="utf-8"))
        if not meta.get(RAW_FILE_SAVED, True):
            return None
        return max(datetime.fromisoformat(meta["finished_at"]), committed)


@lru_cache(maxsize=4)
def _added(record: Path) -> dict[str, datetime]:
    """Each sidecar path with the committer time of the first-parent commit on main that added it (a merge counts from
    the merge, as in `manifest_rows`)."""
    log = subprocess.run(["git", "log", "--first-parent", "--diff-filter=A", "--name-only", "--format=%x00%ct",
                          RECORD_MAIN, "--", QUOTES.as_posix()], cwd=record, capture_output=True, text=True,
                         check=False)  # fmt: skip
    if log.returncode != 0:  # no main in the record: nothing counts
        return {}
    added: dict[str, datetime] = {}
    for entry in log.stdout.split("\0")[1:]:
        stamp, *paths = entry.strip().splitlines()
        for name in paths:
            added[name] = datetime.fromtimestamp(int(stamp), UTC)  # newest first: the oldest commit is kept last
    return added
