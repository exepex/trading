"""Composition root of the playbook (story D1): the one place its concrete parts are chosen and joined."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..config import ROOT
from ..constants import PLAYBOOK_FOLDER
from ..storage.wiring import LIVE_VALIDATION_FOLDER
from .approval_checks import EvidenceCommitted, EvidenceFilled, LiveFeaturesValidated
from .history import PlaybookGit
from .lifecycle import StatusChanger
from .live_reports import CommittedLiveReports, LiveReports, RecomputedLiveReports
from .loader import PlaybookLoader, registry_path
from .registry import Registry, rewritten_history


def _recompute_live_report(live_feature: str) -> Mapping:
    from ..composition import run_live_validation
    from ..config import load_app_config
    from ..models import now_ist

    return run_live_validation(load_app_config(), live_feature, now_ist().date()).summary()


def build_playbook_loader(root: Path = ROOT, reports: LiveReports | None = None) -> PlaybookLoader:
    folder = root / PLAYBOOK_FOLDER
    reports = reports or RecomputedLiveReports(CommittedLiveReports(LIVE_VALIDATION_FOLDER), _recompute_live_report)
    checks = (EvidenceFilled(), EvidenceCommitted(PlaybookGit(root)), LiveFeaturesValidated(reports))
    return PlaybookLoader(folder, Registry(registry_path(folder)), checks)


def build_status_changer(root: Path = ROOT, reports: LiveReports | None = None) -> StatusChanger:
    return StatusChanger(build_playbook_loader(root, reports), PlaybookGit(root))


def registry_history_problems(root: Path = ROOT) -> list[str]:
    """Past registry rows edited in git history or in the working file (empty when append-only)."""
    path = registry_path(root / PLAYBOOK_FOLDER)
    versions = PlaybookGit(root).file_versions(path.relative_to(root).as_posix())
    current = [path.read_text(encoding="utf-8")] if path.is_file() else []
    return rewritten_history(versions + current)
