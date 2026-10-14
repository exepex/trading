"""Composition root of the playbook (story D1): the one place its concrete parts are chosen and joined."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..config import ROOT
from ..constants import PLAYBOOK_FOLDER
from ..storage.wiring import LIVE_VALIDATION_FOLDER
from .allocation import Allocator
from .approval_checks import EvidenceCommitted, EvidenceFilled, ExpectedNetSet, LiveFeaturesValidated
from .candidates import CandidateBuilder
from .evaluate import RuleEvaluator
from .history import PlaybookGit
from .lifecycle import StatusChanger
from .live_reports import CommittedLiveReports, LiveReports, RecomputedLiveReports
from .live_values import ComputedLiveFeatures
from .loader import PlaybookLoader, registry_path
from .opportunities import OpportunityFinder
from .registry import Registry, rewritten_history


def _recompute_live_report(live_feature: str) -> Mapping:
    from ..composition import run_live_validation
    from ..config import load_app_config
    from ..models import now_ist

    return run_live_validation(load_app_config(), live_feature, now_ist().date()).summary()


def build_playbook_loader(root: Path = ROOT, reports: LiveReports | None = None) -> PlaybookLoader:
    folder = root / PLAYBOOK_FOLDER
    reports = reports or RecomputedLiveReports(CommittedLiveReports(LIVE_VALIDATION_FOLDER), _recompute_live_report)
    checks = (EvidenceFilled(), ExpectedNetSet(), EvidenceCommitted(PlaybookGit(root)), LiveFeaturesValidated(reports))
    return PlaybookLoader(folder, Registry(registry_path(folder)), checks)


def build_status_changer(root: Path = ROOT, reports: LiveReports | None = None) -> StatusChanger:
    return StatusChanger(build_playbook_loader(root, reports), PlaybookGit(root))


def registry_history_problems(root: Path = ROOT) -> list[str]:
    """Past registry rows edited in git history or in the working file (empty when append-only)."""
    path = registry_path(root / PLAYBOOK_FOLDER)
    versions = PlaybookGit(root).file_versions(path.relative_to(root).as_posix())
    current = [path.read_text(encoding="utf-8")] if path.is_file() else []
    return rewritten_history(versions + current)


def build_rule_evaluator(cfg: dict, root: Path = ROOT) -> RuleEvaluator:
    """Story D2: the opportunity finder on NSE's session calendar, the structures and cost model of the research (B2),
    and the risk manager with every owner limit (C2), all from config.yaml."""
    from ..composition import build_session_calendar, build_structures
    from ..constants import NIFTY_SYMBOL
    from ..research_engine.cycles import TradingDays
    from ..risk.settings import risk_settings
    from ..risk.trade_costs import SimulatorTradeCosts
    from ..risk.wiring import build_risk_manager

    costs, cap = SimulatorTradeCosts(cfg["charges"]), risk_settings(cfg, root).max_loss_per_trade_rs
    structures = {structure.code: structure for structure in build_structures()}
    builder = CandidateBuilder(structures, costs, cap, cfg["lot_sizes"][NIFTY_SYMBOL])
    finder = OpportunityFinder(TradingDays(build_session_calendar()))
    return RuleEvaluator(finder, builder, Allocator(build_risk_manager(cfg, root), costs))


def build_live_feature_values(cfg: dict, data) -> ComputedLiveFeatures:
    """B7's live 15:00 features over the research data the caller loaded for the day."""
    from ..composition import build_live_features

    return ComputedLiveFeatures(build_live_features(cfg), data)
