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

import requests

from ..research_data.calendar import CalendarError
from ..storage.owner_token import DriveSignInRefused
from .checks import GAP_FIELDS, OVERLAP_FIELDS, gap_rows, overlap_rows
from .collector import CueCollector
from .source import GlobalCueSource
from .table import CueTable, TableFileBroken

LOOK_BACK = timedelta(days=31)
RUN_STOPPERS = (TableFileBroken, OSError, RuntimeError, DriveSignInRefused, requests.RequestException, CalendarError)
GAPS_FILE, OVERLAP_FILE = "gaps.csv", "overlap_usdinr.csv"
RBI_CUE, FBIL_CUE = "usdinr_rbi", "usdinr_fbil"


class GlobalCueJob:
    def __init__(self, collector: CueCollector, tables: dict[str, CueTable], checks: CueChecks):
        self.collector, self.tables, self.checks = collector, tables, checks

    def run(self, sources: list[GlobalCueSource], start: date | None, end: date) -> tuple[list[str], bool]:
        lines, ok = [], True
        for source in sources:
            try:
                line, cue_ok = self._run_cue(source, start, end)
            except RUN_STOPPERS as exc:  # what earlier cues wrote is still reported below
                lines.append(f"{source.cue}: FAILED, run stopped ({type(exc).__name__}): {exc}")
                ok = False
                break
            lines.append(line)
            ok = ok and cue_ok
        return [*lines, *self.checks.write()], ok

    def _run_cue(self, source: GlobalCueSource, start: date | None, end: date) -> tuple[str, bool]:
        table = self.tables[source.cue]
        collection = self.collector.collect(source, start or _default_start(source, table), end)
        if collection.failure:
            return f"{source.cue}: FAILED, {collection.failure}", False
        merged = table.merge(collection.values, collection.fetched_at)
        rows = table.rows()
        last = date.fromisoformat(rows[-1]["value_date"]) if rows else None
        line = f"{source.cue}: {merged.added} dates added, {merged.revisions} revisions logged, last {last}"
        if last is None or (end - last).days > source.max_age_days:
            return f"{line}; STALE: older than {source.max_age_days} days on {end}", False
        return line, True


class CueChecks:
    """The checks' files, rewritten from the tables on every run (reports, not records)."""

    def __init__(self, tables: dict[str, CueTable], folder: Path):
        self.tables, self.checks_folder = tables, Path(folder)

    def write(self) -> list[str]:
        gaps = [g for cue, table in sorted(self.tables.items()) for g in gap_rows(cue, table.rows())]
        rbi, fbil = (_by_date(self.tables[c].rows()) if c in self.tables else {} for c in (RBI_CUE, FBIL_CUE))
        overlap = overlap_rows(rbi, fbil)
        _write(self.checks_folder / GAPS_FILE, GAP_FIELDS, gaps)
        _write(self.checks_folder / OVERLAP_FILE, OVERLAP_FIELDS, overlap)
        counts = Counter((g[0], g[2]) for g in gaps)
        return [
            "gaps: " + (", ".join(f"{cue} {kind} {n}" for (cue, kind), n in sorted(counts.items())) or "none"),
            f"USD/INR RBI against FBIL: {len(set(rbi) & set(fbil))} dates compared, "
            f"{dict(Counter(o[1] for o in overlap)) or 'no difference'}",
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
