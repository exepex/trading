"""Composition root of story G4 (forecast scoring and reports). Apart from `fno/forecast/`, whose files the forecast
protocol freezes (v1 and v2; the v2 freeze test requires every module there to be frozen), so G4 never touches one.

The scored history starts on 1 Jan 2024: 2019-2023 is experiment 1's holdout and the orchestrator's rule keeps G4 off
its back-fill and golden rows. Live records are scored only under the v2 freeze and against their capture receipts.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from datetime import date
from pathlib import Path

from ..config import ROOT
from ..constants import PIPELINE_AREA
from ..forecast.backfill import BACKFILL_FILE
from ..forecast.baseline_wiring import CLOSES_FILE, build_forecast_history
from ..forecast.capture import LIVE_FOLDER
from ..forecast.closes_source import CommittedClosesFile
from ..forecast.freeze import require_frozen_before
from ..forecast.freeze_v2 import require_version_frozen
from ..research_engine.ledger import Git
from ..storage import wiring as storage
from ..storage.raw_store import AreaStore
from ..storage.wiring import PANEL_FOLDER, build_session_calendar
from .resolution import OfficialOutcomes, panel_iv30
from .score_report import ReportContext, report_document
from .score_sources import CaptureReceipts, NoReceipts, RunSummaryReceipts, backfill_forecasts, live_forecasts
from .scoring import ForecastScorer

HISTORY_START = date(2024, 1, 1)
SCORES_FOLDER = "research/forecasts/scores"
COMMON_START = None  # the first day Books 1, 2 and 3 all forecast live; None until Books 2 and 3 exist (story G5)
REVIEW_MONTHS = 6  # design 12.8: no comparison is called significant before six months of common-start trading


def confirmatory_allowed(as_of: date, common_start: date | None = COMMON_START) -> bool:
    if common_start is None:
        return False
    months = (as_of.year - common_start.year) * 12 + as_of.month - common_start.month
    return months > REVIEW_MONTHS or (months == REVIEW_MONTHS and as_of.day >= common_start.day)


def build_receipts(env=os.environ) -> CaptureReceipts:
    """The capture receipts in Drive's pipeline area (owner OAuth settings), or none: live days then stay unscored."""
    drive = storage.build_owner_drive(env)
    return NoReceipts() if drive is None else RunSummaryReceipts(AreaStore(drive, PIPELINE_AREA))


def last_commit(root: Path, path: str) -> str:
    """The commit that last changed `path` (the scored file's commit, which the freeze must precede)."""
    done = subprocess.run(["git", "log", "-1", "--format=%H", "--", path], cwd=root, capture_output=True, text=True)
    return done.stdout.strip()


def _sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def score_forecasts(cfg: dict, as_of: date, receipts: CaptureReceipts, root: Path = ROOT) -> dict:
    """The G4 report document as of `as_of` (only data through that day is read for outcomes)."""
    git = Git(root)
    backfill_commit = last_commit(root, BACKFILL_FILE)
    v1 = require_frozen_before(root, backfill_commit, git)  # protocol v1 section 10: scored only under the freeze
    live_files = sorted((root / LIVE_FOLDER).glob("*/*_forecasts.csv"))
    v2 = require_version_frozen(root, git.head(), git=git) if live_files else None
    history = build_forecast_history(cfg, list(range(HISTORY_START.year, as_of.year + 1)))
    closes = CommittedClosesFile(CLOSES_FILE).closes()
    resolver = OfficialOutcomes(closes, build_session_calendar(), as_of, panel_iv30(history), history.horizon_day)
    backfill = [f for f in backfill_forecasts((root / BACKFILL_FILE).read_bytes(), HISTORY_START) if f.day <= as_of]
    live = live_forecasts(root / LIVE_FOLDER, receipts)
    modes = ForecastScorer(resolver).score(backfill + [f for f in live.forecasts if f.day <= as_of])
    inputs = {
        "backfill_file": BACKFILL_FILE, "backfill_sha256": _sha256(root / BACKFILL_FILE),
        "backfill_commit": backfill_commit, "history_start": HISTORY_START.isoformat(),
        "closes_sha256": _sha256(CLOSES_FILE), "panel_manifest_sha256": _sha256(PANEL_FOLDER / "manifest.json"),
        "protocol_v1_commit": v1.protocol_commit, "protocol_v2_commit": v2.protocol_commit if v2 else None,
        "live_days": len(live_files),
    }  # fmt: skip
    context = ReportContext(as_of, inputs, confirmatory_allowed(as_of), live.late, tuple(live.unverified))
    return report_document(context, modes)
