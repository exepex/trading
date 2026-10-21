"""BANKNIFTY's derived close table in Drive (part A4): the latest receipted table file is read through the verified
Drive cache; an update reads the archived index-close files after the table's last day and writes a new
content-named file (write-once) when it found new closes."""

from __future__ import annotations

import hashlib
from datetime import date, timedelta

from ..price_distribution.store import DistributionStore
from ..storage.drive_cache import DriveCache
from ..storage.receipts import ReceiptFolder
from .closes import TABLE_HEADER, IndexFileCloses, table_rows
from .folders import CLOSES, closes_path, drive

FIRST_DAY = date(2017, 1, 2)  # warmup_closes.csv's first session: the same history for both indices
UNVERIFIED = "the Drive cache could not verify the close tables: {problems}"
WRITTEN = "{underlying} closes: {n} new rows through {through}"
UNCHANGED = "{underlying} closes: no new row (table through {through})"


class CloseTables:
    def __init__(
        self, store: DistributionStore, receipts: ReceiptFolder, cache: DriveCache, first_day: date = FIRST_DAY
    ):
        self.store, self.receipts, self.cache, self.first_day = store, receipts, cache, first_day

    def latest_path(self, underlying: str) -> str | None:
        prefix = f"{underlying.lower()}_through_"
        paths = [r.path for r in self.receipts.under(drive(CLOSES)) if r.path.rsplit("/", 1)[-1].startswith(prefix)]
        return max(paths, default=None)  # ISO dates in the name: the latest table sorts last

    def latest_text(self, underlying: str) -> str | None:
        path = self.latest_path(underlying)
        if path is None:
            return None
        report = self.cache.sync(drive(CLOSES))
        if not report.complete:
            raise RuntimeError(UNVERIFIED.format(problems="; ".join(report.problems)))
        return self.cache.local(path).read_text(encoding="utf-8")

    def update(self, underlying: str, files: IndexFileCloses, through: date) -> list[str]:
        """Appends every regular session after the table's last day up to `through`; returns its lines and gaps."""
        text = self.latest_text(underlying)
        rows = table_rows(text) if text else []
        first = rows[-1].day + timedelta(days=1) if rows else self.first_day
        if first > through:
            return [UNCHANGED.format(underlying=underlying, through=rows[-1].day if rows else None)]
        found, gaps = files.rows(underlying, first, through)
        if not found:
            return [*gaps, UNCHANGED.format(underlying=underlying, through=rows[-1].day if rows else None)]
        lines = [f"{d.isoformat()},{v!r},{name}" for d, v, name in found]
        data = ((text or TABLE_HEADER + "\n") + "\n".join(lines) + "\n").encode()
        self.store.put(closes_path(underlying, found[-1][0], hashlib.sha256(data).hexdigest()), data)
        return [*gaps, WRITTEN.format(underlying=underlying, n=len(found), through=found[-1][0])]
