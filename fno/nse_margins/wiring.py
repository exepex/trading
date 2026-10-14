"""Composition root of story A14: the daily NSE margin job. The only place that picks its concrete parts: Drive's raw
area (the first archived `i1` file, A9; A11 keeps later versions apart), NSE's exposure rule for index options, B2's
structures and research widths, the entry window's near edge, `margins.csv` from `config.yaml` and #fno-desk."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from ..composition import build_alert_sender, build_structures
from ..config import ROOT
from ..constants import NIFTY_SYMBOL
from ..models import now_ist
from ..research_data.expiries import DAYS_TO_EXPIRY
from ..research_engine.cycle_costs import WIDTHS
from ..research_engine.cycles import TradingDays
from ..storage import wiring as storage
from ..storage.raw_source import NseSpanBodSource
from ..storage.raw_store import AreaStore, RawFileStore
from .calculator import NseIndexOptionExposure, SpanMarginCalculator
from .job import DayFile, NseMarginJob, due_session
from .margin_log import MarginLog
from .rows import MarginRowBuilder

DRIVE_SETTINGS_MISSING = f"set {', '.join(storage.OWNER_UPLOAD_SETTINGS)} to read the archived SPAN files in Drive"


def archived_span_file(raw: RawFileStore) -> DayFile:
    """A day's beginning-of-day SPAN file as first archived in Drive (never fetched from NSE here)."""
    return lambda day: (NseSpanBodSource.filename_for(day), raw.get(NseSpanBodSource.path_for(day)))


def build_row_builder(cfg: dict) -> MarginRowBuilder:
    """SF, SC and BF at every research width, one NIFTY lot (`lot_sizes`), first monthly expiry 30+ days out."""
    calculator = SpanMarginCalculator(NseIndexOptionExposure(), cfg["lot_sizes"][NIFTY_SYMBOL])
    return MarginRowBuilder(build_structures(), WIDTHS, calculator, DAYS_TO_EXPIRY[0])


def build_margin_log(cfg: dict, root: Path = ROOT) -> MarginLog:
    return MarginLog(root / cfg["risk"]["margins"]["file"])


def build_trading_days():
    return TradingDays(storage.build_session_calendar()).is_trading_day


def build_nse_margin_job(cfg: dict, env=os.environ, day_file: DayFile | None = None) -> NseMarginJob:
    """Story A14's job on Drive's archived files, or on `day_file` (a local check of downloaded files)."""
    if day_file is None:
        drive = storage.build_owner_drive(env)
        if drive is None:
            raise RuntimeError(DRIVE_SETTINGS_MISSING)
        day_file = archived_span_file(AreaStore(drive, storage.RAW_AREA))
    return NseMarginJob(day_file, build_row_builder(cfg), build_margin_log(cfg), build_trading_days(),
                        build_alert_sender(), now_ist)  # fmt: skip


def due_day() -> date:
    """The first session from today on (the librarian's last day in the scheduled morning job)."""
    return due_session(now_ist(), build_trading_days())
