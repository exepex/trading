"""`backfill-verify` (story A16b): every candle-close row recomputed from the Drive copies it names, read-only. A copy
missing from Drive or the manifest, bytes that differ from the manifest, or a row that differs from its recomputation
is named."""

from __future__ import annotations

from datetime import date

from .backfill import STORE_FAILURES, CandleBackfill
from .nse_days import NseReadFailed
from .session_deriver import SessionInputs
from .session_rv import previous_recorded_session


class CandleRowVerifier:
    def __init__(self, backfill: CandleBackfill):
        """The back-fill's own parts (archive, NSE reader, table, deriver, calendar): one source of truth."""
        self.backfill = backfill
        self.archive, self.nse, self.table, self.deriver = (
            backfill.archive,
            backfill.nse,
            backfill.table,
            backfill.deriver,
        )

    def problems(self) -> list[str]:
        rows = {date.fromisoformat(r["session"]): r for r in self.table.rows()}
        first = self.backfill.first_session()
        found = []
        for day, row in sorted(rows.items()):
            try:
                found += self._check(day, row, rows, first)
            except (*STORE_FAILURES, NseReadFailed) as failed:
                found.append(
                    f"{day}: not verified: {failed if isinstance(failed, NseReadFailed) else type(failed).__name__}"
                )
        return found

    def _check(self, day: date, row: dict, rows: dict, first: date | None) -> list[str]:
        copies = []
        for path in (row["copy_15m"], row["copy_1m"]):
            if not path:
                copies.append(None)
                continue
            manifest_row = self.archive.row_for(path)
            if manifest_row is None:
                return [f"{day}: {path} has no manifest row"]
            copies.append(self.archive.load(manifest_row))
        previous_close = None
        if day != first:
            previous = rows.get(previous_recorded_session(self.backfill.calendar, day))
            if previous is None:
                return [f"{day}: its previous session has no row"]
            previous_row = self.archive.row_for(previous["copy_15m"])
            if previous_row is None:
                return [f"{day}: its previous session's copy has no manifest row"]
            window = self.archive.load(previous_row)
            previous_close = self.deriver.last_level(previous, window)
        again = self.deriver.derive(SessionInputs(day, copies[0], copies[1], self.nse.read(day), previous_close))
        differing = [k for k, v in again.items() if str(v) != row.get(k, "")]
        return [f"{day}: differs from its copies in {', '.join(differing)}"] if differing else []
