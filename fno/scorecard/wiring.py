"""Composition root of the scorecards and pause rules (story E6): the accounts read (the three books and every shadow
version's account), the playbook and its status changer (D1), the alert sender, the charges table, and the execution
snapshots the half-spread reads its touches from (story E2b)."""

from __future__ import annotations

from pathlib import Path

from ..books.account import PaperAccount
from ..books.paths import shadow_account
from ..composition import build_alert_sender
from ..config import ROOT
from ..constants import BOOKS, JOURNAL_FOLDER, SHADOW_FOLDER
from ..desk.records import DeskRecords
from ..desk.wiring import build_execution_snapshots
from ..playbook.wiring import build_playbook_loader, build_status_changer
from .pauses import AutoPauser
from .review import review_terms
from .run import ScorecardRun


def accounts(root: Path = ROOT) -> list[str]:
    shadow = root / JOURNAL_FOLDER / SHADOW_FOLDER
    versions = sorted(p.name for p in shadow.iterdir() if p.is_dir()) if shadow.is_dir() else []
    return [*BOOKS, *(shadow_account(v) for v in versions)]


def build_scorecard_run(cfg: dict, root: Path = ROOT) -> ScorecardRun:
    pauser = AutoPauser(build_status_changer(root), build_alert_sender())
    return ScorecardRun(
        lambda: accounts(root), lambda name: DeskRecords(PaperAccount(root, name)), build_playbook_loader(root),
        pauser, cfg["charges"], review_terms(cfg), build_execution_snapshots(),
    )  # fmt: skip
