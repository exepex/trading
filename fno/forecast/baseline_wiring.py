"""Composition root of the forecast baselines, the back-fill and Book 1's capture (stories G2 and G3). Kept apart
from `fno/forecast/wiring.py`, whose bytes the G1 freeze pins; this file is not frozen."""

from __future__ import annotations

import hashlib
import os
from datetime import date, datetime, timedelta

from ..config import ROOT
from ..constants import PIPELINE_AREA
from ..models import now_ist
from ..pipeline.dispatcher import DispatchReport
from ..pipeline.run_summary import RunSummary, RunSummaryStore
from ..research_data.panel_reader import read_nifty_panel
from ..research_engine.implied_vol import Black76
from ..research_engine.live_features import LiveAtmIvMinusRealised
from ..storage import wiring as storage
from ..storage.raw_store import AreaStore
from ..storage.wiring import PANEL_FOLDER, build_session_calendar
from .baselines import BaseRateBaseline, RiskNeutralBaseline
from .capture import LiveCapture
from .closes_source import CommittedClosesFile
from .history import ForecastHistory
from .live_pack import CUTOFF, LivePackBuilder
from .models import ModelBaseline
from .wiring import GOLDEN_OPTION_DAYS, build_atm_iv30

PANEL_MANIFEST = PANEL_FOLDER / "manifest.json"


def build_forecast_history(cfg: dict, years: list[int] | None = None) -> ForecastHistory:
    """The panel (all years by default, warm-up closes before them) as the baselines may read it (story G2)."""
    panel = read_nifty_panel(PANEL_FOLDER, years, keep=lambda d, e: (e - d).days <= GOLDEN_OPTION_DAYS)
    return ForecastHistory(panel, build_session_calendar(), build_atm_iv30(cfg))


def build_baselines(history: ForecastHistory) -> tuple:
    """The protocol's three baselines (a), (b) and (c), in that order."""
    return RiskNeutralBaseline(history), BaseRateBaseline(history), ModelBaseline(history)


def panel_pack_sha256() -> str:
    """History's input pack: the panel manifest (PROTOCOL.md section 1)."""
    return hashlib.sha256(PANEL_MANIFEST.read_bytes()).hexdigest()


CAPTURE_JOB, CAPTURE_ROUTINE = "forecast-capture", "none (deterministic, no AI)"


def save_capture_summary(run_id: str, started: datetime, line: str, env=os.environ) -> str:
    """The capture's run record in Drive's pipeline area, as every O6 job saves one (`runs/<job>/...`)."""
    drive = storage.build_owner_drive(env)
    if drive is None:
        return f"run summary not saved: set {', '.join(storage.OWNER_UPLOAD_SETTINGS)}"
    summary = RunSummary(CAPTURE_JOB, run_id, CAPTURE_ROUTINE, "success", started, now_ist(), DispatchReport(), (line,))
    return f"run summary: {RunSummaryStore(AreaStore(drive, PIPELINE_AREA)).save(summary)}"


LIVE_PANEL_YEARS = 5  # question 5's base rate needs about 3 years of interpolated IV30 days before the forecast day
CLOSES_FILE = PANEL_FOLDER / "warmup_closes.csv"  # official closes; the O6 daily index-close download extends them


def build_live_capture(cfg: dict) -> LiveCapture:
    """Protocol v2's live capture: A4 snapshots in the repository, official closes, the panel for past IV30."""
    calendar, today = build_session_calendar(), now_ist().date()
    years = list(range(today.year - LIVE_PANEL_YEARS + 1, today.year + 1))
    rule = LiveAtmIvMinusRealised(CUTOFF, cfg["risk_free_rate"], Black76())

    def panel():
        return read_nifty_panel(PANEL_FOLDER, years, keep=lambda d, e: (e - d).days <= GOLDEN_OPTION_DAYS)

    return LiveCapture(ROOT, storage.build_quote_store(), CommittedClosesFile(CLOSES_FILE), panel, calendar,
                       build_atm_iv30(cfg), LivePackBuilder(rule), calendar.calendar_sha256(), now_ist)  # fmt: skip


V4_FOLDER = ROOT / "research" / "forecasts" / "v4"  # story G7's records, G8's input (one file per forecaster/question)
V4_METHOD_FILES = ("series.py", "baselines.py", "rules.py", "capture.py")  # their bytes are each record's method hash
V4_LATER_DAYS = 10  # calendar days after the last close: today's session when it is not yet in the closes file


def build_v4_forecasts(today: date | None = None):
    """Protocol v4's phase-1 forecasters (story G7) on the committed closes and A16's live `rv/` rows."""
    from ..forecast_v4.sessions import is_scored_session
    from ..forecast_v4_rules import series
    from ..forecast_v4_rules.capture import DayForecasts, Inputs
    from ..intraday.rv_table import RvTable
    from ..intraday.wiring import INTRADAY_FOLDER

    text = CLOSES_FILE.read_text()
    rows = series.closes_rows(text)
    closes = series.regular_closes(rows)
    lines = [line for line in text.splitlines()[1:] if line.split(",")[1:2] == ["regular"]]
    calendar = build_session_calendar()
    end = max(closes[-1].day, today or closes[-1].day)
    days = [closes[0].day + timedelta(days=i) for i in range((end - closes[0].day).days + V4_LATER_DAYS)]
    sessions = [d for d in days if d <= end and is_scored_session(calendar, d)]
    package = ROOT / "fno" / "forecast_v4_rules"
    method = hashlib.sha256(b"".join((package / name).read_bytes() for name in V4_METHOD_FILES)).hexdigest()
    intraday = series.live_intraday_rv(RvTable(INTRADAY_FOLDER).rows()) if INTRADAY_FOLDER.exists() else []
    return DayForecasts(Inputs(closes, lines, intraday, sessions, method))


def v4_writer(folder=V4_FOLDER):
    from ..forecast_v4_rules import records

    return lambda forecaster, question, rows: records.write(folder, forecaster, question, rows)
