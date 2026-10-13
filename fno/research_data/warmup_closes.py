"""Warm-up closes before the NIFTY panel's first session (story A10): the NIFTY 50 and India VIX close of every NSE
session from 2017 to 2018, read from NSE's index-close files, so the 2019 features have their history (F2 needs the
previous 250 India VIX closes, F1 the previous 21 NIFTY 50 closes).

Index closes only, never an option or future row: the 2017-18 F&O files are never opened (no experiment may see a
2018 outcome). A session without its file or either close fails the whole build, naming the days; nothing is written.
The file is derived data, committed next to the panel (`warmup_closes.csv`); the raw files stay in Drive.
"""

from __future__ import annotations

import csv
import io
import tempfile
from datetime import date
from pathlib import Path

from ..constants import INDEX_INDIA_VIX, INDEX_NIFTY_50
from ..fo_bhavcopy import BadFile, read_index_closes
from .calendar import SessionCalendar
from .nifty_panel import DailyFiles, PanelBuildError
from .panel_store import WARMUP_FIELDS, WARMUP_FILE, file_sha256


def build_warmup_rows(index_files: DailyFiles, calendar: SessionCalendar, start: date, end: date) -> list[tuple]:
    """One row per session from start to end; PanelBuildError naming every session without both closes."""
    rows, problems = [], []
    for day in calendar.sessions(start, end):
        filename, data = index_files.get(day)
        if data is None:
            problems.append(f"{day}: no index-close file {filename}")
            continue
        try:
            closes = read_index_closes(data, filename)
        except BadFile as exc:
            problems.append(f"{day}: {exc}")
            continue
        missing = [name for name in (INDEX_NIFTY_50, INDEX_INDIA_VIX) if name not in closes]
        if missing:
            problems.append(f"{day}: {filename} has no close for {missing}")
            continue
        session = calendar.session_kind(day)
        nifty, vix = closes[INDEX_NIFTY_50], closes[INDEX_INDIA_VIX]
        rows.append((day.isoformat(), session, nifty, vix, filename, file_sha256(data)))
    if problems:
        raise PanelBuildError(problems)
    return rows


def write_warmup_closes(folder: Path, rows: list[tuple]) -> Path:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(WARMUP_FIELDS)
    writer.writerows(rows)
    path = Path(folder) / WARMUP_FILE
    with tempfile.NamedTemporaryFile("w", dir=folder, delete=False, encoding="utf-8", suffix=".part") as temporary:
        temporary.write(out.getvalue())
    Path(temporary.name).replace(path)  # never a half-written file
    return path
