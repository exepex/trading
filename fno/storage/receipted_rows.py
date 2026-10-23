"""O9b's receipt-backed tables (story O9b, section 2): an append-only table as a series of write-once Drive parts, and a
report rewritten every run as a series of snapshots, both written through O9's `DataStore` (one SHA-256 receipt per
file) and read through the verified `DriveCache` (the receipts are the index; Drive is never listed, and a missing or
changed file stops the reader). Parts are named by the writing run's id, which sorts by time, so a table's rows are
its parts' rows in name order; a table moved from the repository starts with today's file as its first part, so the
rebuilt table equals the old file byte for byte."""

from __future__ import annotations

import csv
import io

from .data_store import DataStore
from .drive_cache import DriveCache
from .report_files import Report
from .row_log import RowLog, TableFileBroken

PART = "{folder}/{run_id}{n}.csv"  # one part per run; a second write in the same run gets "_02" (sorts after ".csv")
TABLE_UNREADABLE = "{folder}: the Drive copies could not be verified: {problems}"
NO_LAST_NEWLINE = "{what} does not end with a new line: the next part's first row would join its last row"
OUT_OF_ORDER = "{path}: would sort before {held}, so its rows would be read out of order; nothing written"


class DriveDataUnavailable(RuntimeError):
    """A receipted file was missing from Drive or held other bytes: nothing of the table is read."""


class PartOutOfOrder(RuntimeError):
    """A new file would not sort after the series' files (two runs in one second, or a clock behind): not written."""


class _ReceiptedSeries:
    def __init__(self, store: DataStore, cache: DriveCache, folder: str):
        """`folder`: inside the store's area (e.g. `vix/india_vix_daily`)."""
        self.store, self.cache, self.folder = store, cache, folder
        self._writes = 0

    def write_bytes(self, data: bytes) -> None:
        """One new write-once file of this run (the move of an existing file uses it for the first part)."""
        self._writes += 1
        n = "" if self._writes == 1 else f"_{self._writes:02d}"
        part = PART.format(folder=self.folder, run_id=self.store.run_id, n=n)
        last = max((r.path for r in self.cache.receipts.under(f"{self.store.area}/{self.folder}")), default="")
        if last >= f"{self.store.area}/{part}":
            raise PartOutOfOrder(OUT_OF_ORDER.format(path=part, held=last))
        self.store.put(part, data)

    def files(self) -> list[bytes]:
        """Every receipted file of the series, verified, in name order."""
        prefix = f"{self.store.area}/{self.folder}"
        report = self.cache.sync(prefix)
        if not report.complete:
            raise DriveDataUnavailable(TABLE_UNREADABLE.format(folder=prefix, problems="; ".join(report.problems)))
        return [self.cache.local(r.path).read_bytes() for r in self.cache.receipts.under(prefix)]


class ReceiptedRowLog(_ReceiptedSeries, RowLog):
    """Parts are joined end to end, so every part must end with a new line: one that does not is refused by name, at
    write and at read (the RowLog contract both adapters keep; A14/C2/C4 owner's review, 23 Oct 2026)."""

    def write_bytes(self, data: bytes) -> None:
        if data and not data.endswith(b"\n"):
            raise TableFileBroken(NO_LAST_NEWLINE.format(what=f"the new part of {self.folder}"))
        super().write_bytes(data)

    def rows(self) -> list[dict[str, str]]:
        return list(csv.DictReader(self.rebuilt().decode("utf-8").splitlines()))

    def rebuilt(self) -> bytes:
        """The table as one CSV: the first part whole, then each later part without its header line."""
        parts = self.files()
        if any(part and not part.endswith(b"\n") for part in parts):
            raise TableFileBroken(NO_LAST_NEWLINE.format(what=f"a part of {self.folder}"))
        return b"".join([parts[0], *(part.split(b"\n", 1)[1] for part in parts[1:])]) if parts else b""

    def current_bytes(self) -> bytes:
        return self.rebuilt()

    def check_appendable(self) -> None:
        """Every append is a new write-once part: nothing existing can change."""

    def catch_up(self, held: bytes, data: bytes) -> bytes | None:
        """The part that makes the table equal `data`: all of it when Drive holds nothing, the rows after `held`
        (under `data`'s header) when `held` is a whole-line start of `data`, else None (they disagree)."""
        if not held:
            return data
        if not (held.endswith(b"\n") and data.startswith(held)):
            return None
        return data.split(b"\n", 1)[0] + b"\n" + data[len(held) :]

    def append(self, fields: tuple[str, ...], rows: list[tuple]) -> None:
        if rows:
            self.write_bytes(_csv(fields, rows))


class ReceiptedSnapshots(_ReceiptedSeries, Report):
    """A report rewritten every run: one new file per run, the newest is current (as A17's `DriveSnapshots`)."""

    def write(self, fields: tuple[str, ...], rows: list[tuple]) -> None:
        self.write_bytes(_csv(fields, rows))

    def catch_up(self, held: bytes, data: bytes) -> bytes:
        """A report is replaced whole: `data` becomes the newest snapshot."""
        return data

    def latest_bytes(self) -> bytes | None:
        files = self.files()
        return files[-1] if files else None

    def current_bytes(self) -> bytes:
        return self.latest_bytes() or b""

    def latest(self) -> list[dict[str, str]]:
        data = self.latest_bytes()
        return list(csv.DictReader(data.decode("utf-8").splitlines())) if data else []


def _csv(fields: tuple[str, ...], rows: list[tuple]) -> bytes:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(fields)
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")
