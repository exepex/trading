"""Composition root of the factory (story R1): the ledger (B4), the gate log on D1's git history, the idea cards, C1's
charges from config.yaml and the data-spend register."""

from __future__ import annotations

from pathlib import Path

from ..config import ROOT
from ..research_engine.ledger import Ledger
from .card import IdeaCard, read_card
from .constants import DATA_SPEND_FILE, IDEAS_FOLDER, TEMPLATE_CARD
from .gate_log import GateLog
from .gate_steps import GateSteps
from .registration import IdeaRegistration
from .staging import FactoryGit
from .trial_count import TrialCount


def card_path(idea_id: str) -> str:
    return f"{IDEAS_FOLDER}/{idea_id}.md"


def read_idea(idea_id: str, root: Path = ROOT) -> IdeaCard:
    return read_card(root, card_path(idea_id))


def read_all_ideas(root: Path = ROOT) -> list[IdeaCard]:
    paths = sorted(p for p in (Path(root) / IDEAS_FOLDER).glob("*.md") if p.name != TEMPLATE_CARD)
    return [read_card(root, p.relative_to(root).as_posix()) for p in paths]


def build_gate_log(root: Path = ROOT) -> GateLog:
    return GateLog(root, FactoryGit(Path(root)))


def build_trial_count(root: Path = ROOT) -> TrialCount:
    return TrialCount(Ledger(root).rows())


def build_registration(root: Path = ROOT) -> IdeaRegistration:
    git = FactoryGit(Path(root))
    return IdeaRegistration(Ledger(root, git), GateLog(root, git), git)


def build_gate_steps(root: Path = ROOT) -> GateSteps:
    from ..config import load_app_config

    git = FactoryGit(Path(root))
    register = Path(root) / DATA_SPEND_FILE
    charges = load_app_config()["charges"]
    return GateSteps(GateLog(root, git), git, charges, lambda: register.read_text(encoding="utf-8"))
