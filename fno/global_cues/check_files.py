"""The checks of the cue tables, rewritten on every run (story A17; reports, not records).

Public cues' gaps and the RBI/FBIL comparison go to `research/data/global-cues/checks/`. A private cue's gaps (dates,
never values, but still kept out of this public repository by the owner's rule) go to its own Drive log; only their
counts are printed. Each run writes a full new snapshot there; the newest is current.
"""

from __future__ import annotations

import csv
import io
from collections import Counter
from pathlib import Path

from .checks import GAP_FIELDS, OVERLAP_FIELDS, gap_rows, overlap_rows
from .row_log import DriveSnapshots
from .table import CueTable

GAPS_FILE, OVERLAP_FILE = "gaps.csv", "overlap_usdinr.csv"
RBI_CUE, FBIL_CUE = "usdinr_rbi", "usdinr_fbil"


class CueChecks:
    def __init__(
        self, tables: dict[str, CueTable], folder: Path, private_gaps: dict[str, DriveSnapshots] | None = None
    ):
        """`private_gaps`: cue -> where its gaps go in Drive (those cues never reach the repository's files)."""
        self.tables, self.checks_folder, self.private_gaps = tables, Path(folder), private_gaps or {}

    def write(self) -> list[str]:
        gaps = {cue: gap_rows(cue, table.rows()) for cue, table in sorted(self.tables.items())}
        public = [g for cue, rows in gaps.items() if cue not in self.private_gaps for g in rows]
        for cue, snapshots in self.private_gaps.items():
            snapshots.write(GAP_FIELDS, gaps.get(cue, []))
        rbi, fbil = (_by_date(self.tables[c].rows()) if c in self.tables else {} for c in (RBI_CUE, FBIL_CUE))
        overlap = overlap_rows(rbi, fbil)
        _write(self.checks_folder / GAPS_FILE, GAP_FIELDS, public)
        _write(self.checks_folder / OVERLAP_FILE, OVERLAP_FIELDS, overlap)
        counts = Counter((g[0], g[2]) for rows in gaps.values() for g in rows)
        return [
            "gaps: " + (", ".join(f"{cue} {kind} {n}" for (cue, kind), n in sorted(counts.items())) or "none"),
            f"USD/INR RBI against FBIL: {len(set(rbi) & set(fbil))} dates compared, "
            f"{dict(Counter(o[1] for o in overlap)) or 'no difference'}",
        ]


def _by_date(rows: list[dict[str, str]]) -> dict[str, str]:
    return {r["value_date"]: r["value"] for r in rows}


def _write(path: Path, fields: tuple[str, ...], rows: list[tuple]) -> None:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(fields)
    writer.writerows(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.part")
    temporary.write_text(out.getvalue(), encoding="utf-8")
    temporary.replace(path)  # never a half-written report
