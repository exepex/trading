"""Every download attempt of a once-a-day cue (story A17b): its time and outcome, never a value.

The once-a-day rule caps failures too: after `MAX_ATTEMPTS` attempts on one IST date, or after one saved copy (the
snapshot log's business), nothing more is downloaded that day. One CSV per cue under
`research/data/manifests/global-cues/attempts/`.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from .row_log import CsvRowLog

FIELDS = ("attempted_at", "outcome")
MAX_ATTEMPTS = 3
SAVED, DOWNLOAD_FAILED, NOT_PUBLISHERS_FILE, NO_VALUES, SAVE_FAILED = (
    "saved",
    "download_failed",
    "not_publishers_file",
    "no_values",
    "save_failed",
)


class AttemptLog:
    def __init__(self, folder: Path):
        self.folder = Path(folder)

    def _log(self, cue: str) -> CsvRowLog:
        return CsvRowLog(self.folder / f"{cue}.csv")

    def append(self, cue: str, attempted_at: datetime, outcome: str) -> None:
        log = self._log(cue)
        log.check_appendable()
        log.append(FIELDS, [(attempted_at.isoformat(), outcome)])

    def count_on(self, cue: str, day: date) -> int:
        return sum(datetime.fromisoformat(r["attempted_at"]).date() == day for r in self._log(cue).rows())
