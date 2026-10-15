"""Writes the India VIX table's checks (story A15, `checks.py`) as CSV files next to the table, and the summary lines.

The files are rewritten from the table on every run (they are reports, not records); the table itself is never
changed by a check.
"""

from __future__ import annotations

import csv
import io
from collections import Counter
from collections.abc import Callable, Mapping
from datetime import date
from pathlib import Path

from ..research_data.calendar import SessionCalendar
from .checks import GAP_FIELDS, LEVEL_FIELDS, OVERLAP_FIELDS, gap_rows, level_rows, overlap_rows

GAPS_FILE, LEVELS_FILE, OVERLAP_FILE = "gaps.csv", "level_flags.csv", "overlap_index_close.csv"
REFERENCE_VIX_COLUMN = "vix"  # the India VIX close in the committed index-close closes (A10's warmup_closes.csv)


def committed_vix_closes(path: Path) -> dict[date, str]:
    """The India VIX close of each session in a committed closes file with `date` and `vix` columns."""
    rows = csv.DictReader(Path(path).read_text(encoding="utf-8").splitlines())
    return {date.fromisoformat(r["date"]): r[REFERENCE_VIX_COLUMN] for r in rows}


class VixCheckFiles:
    def __init__(
        self,
        folder: Path,
        calendar: SessionCalendar,
        calendar_first: date,
        reference: Callable[[], Mapping[date, str]],
    ):
        """`calendar_first`: the first day the session calendar covers."""
        self.folder, self.calendar, self.calendar_first, self.reference = (
            Path(folder),
            calendar,
            calendar_first,
            reference,
        )

    def write(self, rows: list[dict[str, str]]) -> list[str]:
        closes = {date.fromisoformat(r["date"]): r["close"] for r in rows}
        gaps = gap_rows(set(closes), self.calendar, self.calendar_first)
        flags = level_rows(rows)
        reference = self.reference()
        overlap = overlap_rows(closes, reference)
        compared = sorted(set(closes) & set(reference))
        self._csv(GAPS_FILE, GAP_FIELDS, gaps)
        self._csv(LEVELS_FILE, LEVEL_FIELDS, flags)
        self._csv(OVERLAP_FILE, OVERLAP_FIELDS, overlap)
        return [
            f"gaps ({GAPS_FILE}): {_counts(gaps)}",
            f"doubtful levels, kept as published ({LEVELS_FILE}): {_counts(flags)}",
            f"against the index-close VIX closes ({OVERLAP_FILE}): {len(compared)} days compared"
            + (f" ({compared[0]} to {compared[-1]})" if compared else " (NOTHING compared)")
            + f": {_counts(overlap)}",
        ]

    def _csv(self, name: str, fields: tuple[str, ...], rows: list[tuple]) -> None:
        out = io.StringIO()
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(fields)
        writer.writerows(rows)
        self.folder.mkdir(parents=True, exist_ok=True)
        temporary = self.folder / f".{name}.part"
        temporary.write_text(out.getvalue(), encoding="utf-8")
        temporary.replace(self.folder / name)  # never a half-written report


def _counts(rows: list[tuple]) -> str:
    kinds = Counter(r[1] for r in rows)
    return ", ".join(f"{kind} {n}" for kind, n in sorted(kinds.items())) or "none"
