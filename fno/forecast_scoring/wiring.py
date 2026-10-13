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

from ..ai.coverage import pack_days
from ..ai.paths import AI_FOLDER
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
from .ai_sources import ai_forecasts
from .coverage import book_coverage
from .resolution import OfficialOutcomes, panel_iv30
from .score_inputs import CLOSE_PROXY, LIVE
from .score_report import ReportContext, report_document
from .score_sources import CaptureReceipts, NoReceipts, RunSummaryReceipts, backfill_forecasts, live_forecasts
from .scoring import ForecastScorer

HISTORY_START = date(2024, 1, 1)
SCORES_FOLDER = "research/forecasts/scores"
COMMON_START = date(2026, 10, 14)  # first live day for all three books (orchestrator, judge 58); fixed: a book that
# misses it shows lower coverage, never a later start. No protocol fixes another date (design 12.8 names none).
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
    closes, calendar = CommittedClosesFile(CLOSES_FILE).closes(), build_session_calendar()
    live = live_forecasts(root / LIVE_FOLDER, receipts)
    resolvers = {  # question 5: history against the panel's close IV30, live against its own 15:00 pack IV30
        CLOSE_PROXY: OfficialOutcomes(closes, calendar, as_of, panel_iv30(history), history.horizon_day),
        LIVE: OfficialOutcomes(closes, calendar, as_of, lambda day: (True, live.pack_iv30.get(day)),
                               history.horizon_day),
    }  # fmt: skip
    ai = ai_forecasts(root / AI_FOLDER, live.packs)
    backfill = backfill_forecasts((root / BACKFILL_FILE).read_bytes(), HISTORY_START)
    scored = [f for f in backfill + live.forecasts + ai.forecasts if f.day <= as_of]
    inputs = {
        "backfill_file": BACKFILL_FILE, "backfill_sha256": _sha256(root / BACKFILL_FILE),
        "backfill_commit": backfill_commit, "history_start": HISTORY_START.isoformat(),
        "closes_sha256": _sha256(CLOSES_FILE), "panel_manifest_sha256": _sha256(PANEL_FOLDER / "manifest.json"),
        "protocol_v1_commit": v1.protocol_commit, "protocol_v2_commit": v2.protocol_commit if v2 else None,
        "live_days": len(live_files),
    }  # fmt: skip
    context = ReportContext(
        as_of, inputs, confirmatory_allowed(as_of), live.late, tuple(live.unverified), COMMON_START,
        book_coverage(pack_days(root), scored, COMMON_START, as_of),
        {book: sorted(labels) for book, labels in ai.isolation.items()}, tuple(ai.unscored),
    )  # fmt: skip
    return report_document(context, ForecastScorer(resolvers).score(scored))
