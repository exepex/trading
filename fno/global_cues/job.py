"""One run over the cues (story A17): for each, download, archive and extend its table; then rewrite the checks.

A cue that fails writes nothing and is named; the others still run. The default range starts 31 days before a
table's last date (so late values and revisions are seen) or, for an empty table, at the source's first date.
"""

from __future__ import annotations

import csv
import io
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from .checks import GAP_FIELDS, OVERLAP_FIELDS, gap_rows, overlap_rows
from .collector import CueCollector
from .source import GlobalCueSource
from .table import CueTable

LOOK_BACK = timedelta(days=31)
GAPS_FILE, OVERLAP_FILE = "gaps.csv", "overlap_usdinr.csv"
RBI_CUE, FBIL_CUE = "usdinr_rbi", "usdinr_fbil"


class GlobalCueJob:
    def __init__(self, collector: CueCollector, tables: dict[str, CueTable], checks: CueChecks):
        self.collector, self.tables, self.checks = collector, tables, checks

    def run(self, sources: list[GlobalCueSource], start: date | None, end: date) -> tuple[list[str], bool]:
        lines, ok = [], True
        for source in sources:
            table = self.tables[source.cue]
            collection = self.collector.collect(source, start or _default_start(source, table), end)
            if collection.failure:
                lines.append(f"{source.cue}: FAILED, {collection.failure}")
                ok = False
                continue
            merged = table.merge(collection.values, collection.fetched_at)
            last = table.rows()[-1]["value_date"] if table.rows() else "none"
            lines.append(f"{source.cue}: {merged.added} dates added, {merged.revisions} revisions logged, last {last}")
        return [*lines, *self.checks.write()], ok


class CueChecks:
    """The checks' files, rewritten from the tables on every run (reports, not records)."""

    def __init__(self, tables: dict[str, CueTable], folder: Path):
        self.tables, self.checks_folder = tables, Path(folder)

    def write(self) -> list[str]:
        gaps = [g for cue, table in sorted(self.tables.items()) for g in gap_rows(cue, table.rows())]
        rbi, fbil = (_by_date(self.tables[c].rows()) for c in (RBI_CUE, FBIL_CUE))
        overlap = overlap_rows(rbi, fbil)
        _write(self.checks_folder / GAPS_FILE, GAP_FIELDS, gaps)
        _write(self.checks_folder / OVERLAP_FILE, OVERLAP_FIELDS, overlap)
        counts = Counter((g[0], g[2]) for g in gaps)
        return [
            "gaps: " + (", ".join(f"{cue} {kind} {n}" for (cue, kind), n in sorted(counts.items())) or "none"),
            f"USD/INR RBI against FBIL: {dict(Counter(o[1] for o in overlap)) or 'no difference'}",
        ]


def _default_start(source: GlobalCueSource, table: CueTable) -> date:
    rows = table.rows()
    return date.fromisoformat(rows[-1]["value_date"]) - LOOK_BACK if rows else source.first_value_date


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
