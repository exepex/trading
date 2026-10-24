"""The release records as G8 reads them (story G10 completion, criterion 6): every record whose receipt is in the
checkout, brought from Drive through O9's verified cache before it is used. No receipt yet: no records (nothing to
fetch, so no Drive needed). A receipt whose bytes Drive does not return or returns changed stops the report or look
with the day named, never a report with fewer labels."""

from __future__ import annotations

import posixpath
from collections.abc import Callable
from datetime import date
from pathlib import Path

from ...storage.drive_cache import DriveCache
from ...storage.receipts import ReceiptFolder
from ...v4_pack.paths import DAYS_FOLDER
from ...v4_pack.release import parse_release
from .days import DayFileError, DayLabel, V4DaySource

NOT_VERIFIED = "the v4 release records could not be read from Drive: {problems}"


class ReleasedDays(V4DaySource):
    def __init__(self, receipts: ReceiptFolder, cache: Callable[[], DriveCache], area: str):
        """`cache()`: the Drive cache, built only when a record has to be fetched."""
        self.receipts, self.cache, self.area = receipts, cache, area

    def labels(self) -> dict[date, DayLabel]:
        folder = f"{self.area}/{DAYS_FOLDER}"
        if not self.receipts.under(folder):
            return {}
        cache = self.cache()
        report = cache.sync(folder)
        if report.problems:
            raise DayFileError(NOT_VERIFIED.format(problems="; ".join(report.problems)))
        records = (self._record(cache.local(r.path), r.path) for r in self.receipts.under(folder))
        return {record.day: DayLabel(record.day, record.label, record.pack_sha256, record.observed_by)
                for record in records}  # fmt: skip

    @staticmethod
    def _record(file: Path, path: str):
        return parse_release(posixpath.splitext(posixpath.basename(path))[0], file.read_bytes())
