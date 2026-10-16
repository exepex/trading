"""Composition root of the factory (story R1): the ledger (B4), the gate log and research questions on D1's git
history, the idea cards, C1's charges from config.yaml, the data-spend register, the playbook (D1) and the shadow
accounts' records (E6, E2c)."""

from __future__ import annotations

from pathlib import Path

from ..config import ROOT
from ..research_engine.ledger import Ledger
from .card import IdeaCard, read_card
from .constants import DATA_SPEND_FILE, IDEAS_FOLDER, TEMPLATE_CARD
from .gate_log import GateLog
from .gate_order import GateOrder
from .gate_steps import GateSteps
from .questions import Questions
from .registered_shadows import RegisteredShadows
from .registration import IdeaRegistration
from .registration_freeze import FactoryFreeze
from .staging import FactoryGit
from .trial_count import TrialCount
from .verdict import ShadowResults, ShadowVerdicts


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


def _charges() -> dict:
    from ..config import load_app_config

    return load_app_config()["charges"]


def _order(root: Path) -> GateOrder:
    git = FactoryGit(Path(root))
    return GateOrder(GateLog(root, git), git)


def build_gate_steps(root: Path = ROOT) -> GateSteps:
    register = Path(root) / DATA_SPEND_FILE
    return GateSteps(_order(root), _charges(), lambda: register.read_text(encoding="utf-8"))


def build_questions(root: Path = ROOT) -> Questions:
    return Questions(root, FactoryGit(Path(root)))


def build_freeze(root: Path = ROOT) -> FactoryFreeze:
    from ..playbook.wiring import build_playbook_loader

    playbook = build_playbook_loader(root).load()
    return FactoryFreeze(_order(root), Ledger(root, FactoryGit(Path(root))), build_questions(root), playbook)


def shadow_results(root: Path = ROOT) -> ShadowResults:
    """The shadow accounts' completed positions (R3), after E2c's download of the paper accounts from Drive."""
    from ..books.account import PaperAccount
    from ..desk.records import DeskRecords
    from ..desk.wiring import download_private_records
    from .shadow_nets import StrategyNets

    download_private_records(root=root)
    return StrategyNets(lambda account: DeskRecords(PaperAccount(root, account)), _charges())


def build_verdicts(root: Path = ROOT, results: ShadowResults | None = None) -> ShadowVerdicts:
    ledger = Ledger(root, FactoryGit(Path(root)))
    return ShadowVerdicts(_order(root), ledger, build_questions(root), results or shadow_results(root))


def build_registered_shadows(root: Path = ROOT) -> RegisteredShadows:
    return RegisteredShadows(GateLog(root, FactoryGit(Path(root))))
