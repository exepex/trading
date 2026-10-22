"""Composition root of story O9b step 1b: the public cues' tables, their shared revision log and the public checks as
receipt-backed series in Drive's `data` area (written as the `global-cues` job, read through the verified cache).
Apart from `wiring.py`, which picks the rest of A17's parts, to keep both under the size limit."""

from __future__ import annotations

import os

from ..storage.data_wiring import build_data_store, build_drive_cache
from ..storage.receipted_rows import ReceiptedRowLog, ReceiptedSnapshots
from .check_files import CHECK_FILES

WRITER = "global-cues"
TABLE, REVISIONS = "global-cues/{cue}", "global-cues/revisions"  # inside Drive's `data` area
TRADING_DATES, CHECK = "global-cues/us_trading_dates", "global-cues/checks/{stem}"


class PublicCueSeries:
    """One run's series: one object per Drive folder, so a second write in the run is numbered, never a clash."""

    def __init__(self, env=os.environ):
        self.store, self.cache = build_data_store(WRITER, env=env), build_drive_cache(env)
        self.revisions = ReceiptedRowLog(self.store, self.cache, REVISIONS)

    def table(self, cue: str) -> ReceiptedRowLog:
        return ReceiptedRowLog(self.store, self.cache, TABLE.format(cue=cue))

    def checks(self) -> dict[str, ReceiptedSnapshots]:
        return {name: self._snapshots(CHECK.format(stem=name.rsplit(".", 1)[0])) for name in CHECK_FILES}

    def trading_dates(self) -> ReceiptedSnapshots:
        return self._snapshots(TRADING_DATES)

    def _snapshots(self, folder: str) -> ReceiptedSnapshots:
        return ReceiptedSnapshots(self.store, self.cache, folder)
