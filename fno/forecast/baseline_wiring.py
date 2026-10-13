"""Composition root of the forecast baselines, the back-fill and Book 1's capture (stories G2 and G3). Kept apart
from `fno/forecast/wiring.py`, whose bytes the G1 freeze pins; this file is not frozen."""

from __future__ import annotations

import hashlib
import os
from datetime import datetime

from ..constants import PIPELINE_AREA
from ..models import now_ist
from ..pipeline.dispatcher import DispatchReport
from ..pipeline.run_summary import RunSummary, RunSummaryStore
from ..research_data.panel_reader import read_nifty_panel
from ..storage import wiring as storage
from ..storage.raw_store import AreaStore
from ..storage.wiring import PANEL_FOLDER, build_session_calendar
from .baselines import BaseRateBaseline, RiskNeutralBaseline
from .history import ForecastHistory
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
