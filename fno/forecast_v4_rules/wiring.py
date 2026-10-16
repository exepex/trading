"""Composition root of protocol v4's close-based forecasters (stories G7 and G7b): the committed closes, A16's live
`rv/` rows, the A7 calendar and the record folder. Kept in this package because the v2 freeze pins every file of
`fno/forecast/` (`research/forecasts/FREEZE_v2.md`), as G4 keeps its own in `fno/forecast_scoring/`."""

from __future__ import annotations

import hashlib
from datetime import date, timedelta
from pathlib import Path

from ..config import ROOT
from ..constants import SESSION_REGULAR
from ..forecast_v4.sessions import is_scored_session
from ..intraday.rv_table import RvTable
from ..intraday.wiring import INTRADAY_FOLDER
from ..storage.wiring import PANEL_FOLDER, build_session_calendar
from . import records, series
from .capture import FORECASTERS, DayForecasts, Inputs

V4_FOLDER = ROOT / "research" / "forecasts" / "v4"  # the records, G8's input (one file per forecaster and question)
CLOSES_FILE = PANEL_FOLDER / "warmup_closes.csv"  # official closes; the O6 daily index-close download extends them
METHOD_FILES = (
    "series.py",
    "baselines.py",
    "rules.py",
    "vix_rule.py",
    "capture.py",
)  # their bytes are each record's method hash


def build_v4_forecasts(today: date | None = None) -> DayForecasts:
    """The forecasters on the committed closes and A16's live rows; `today` is added as a session when its close is
    not in the file yet (the live capture's day)."""
    text = CLOSES_FILE.read_text()
    rows = series.closes_rows(text)
    closes, vix = series.regular_closes(rows), series.vix_closes(rows)
    lines = [line for line in text.splitlines()[1:] if line.split(",")[1:2] == [SESSION_REGULAR]]
    calendar = build_session_calendar()
    end = max(closes[-1].day, today or closes[-1].day)
    days = [closes[0].day + timedelta(days=i) for i in range((end - closes[0].day).days + 1)]
    sessions = [d for d in days if is_scored_session(calendar, d)]
    intraday = series.live_intraday_rv(RvTable(INTRADAY_FOLDER).rows()) if INTRADAY_FOLDER.exists() else []
    return DayForecasts(Inputs(closes, vix, lines, intraday, sessions, method_sha256()))


def method_sha256() -> str:
    """SHA-256 of the method files' bytes, carried by every record row (a back-fill made on other code is refused)."""
    package = Path(__file__).resolve().parent
    return hashlib.sha256(b"".join((package / name).read_bytes() for name in METHOD_FILES)).hexdigest()


def v4_writer(folder: Path = V4_FOLDER):
    return lambda forecaster, question, rows: records.write(folder, forecaster, question, rows)


def record_folders() -> list[str]:
    """The repository folders `forecast-v4 capture` writes, one per forecaster id (repository-relative, ending "/"),
    so a daily run commits exactly these and never another step's files (O1, agreed 16 Oct 2026)."""
    folder = V4_FOLDER.relative_to(ROOT).as_posix()
    return [f"{folder}/{forecaster}/" for forecaster in sorted({f for f, _ in FORECASTERS})]
