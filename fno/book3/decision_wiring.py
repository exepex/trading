"""Composition root of Book 3's decision engine (stories F6 and F7): its decider (F1t's port), its orders and exits
(E3's seams, dispatched per book by the daily run), its day sheet's evaluation and its shadow reader. D2's evaluator
parts, C2, C4's validator, D5's registry and constitution, D6's components and Book 1's input reader are reused as
built; swapping any of them changes this file only."""

from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path

from ..config import ROOT
from ..constants import BOOK3_AI, PLAYBOOK_FOLDER
from .constitution import COMPONENT, ConstitutionFiles
from .evaluation import Book3Evaluators

PROMPT_FILE = "agents/book3/decide_v1.md"
PROMPT_COMPONENT = "book3_prompt"


def prompt_sha256(root: Path = ROOT) -> str:
    return hashlib.sha256((Path(root) / PROMPT_FILE).read_bytes()).hexdigest()


def build_book3_evaluators(cfg: dict, root: Path = ROOT) -> Book3Evaluators:
    """D2's own finder, candidate builder, allocator (C2) and real-book check, as Book 1's evaluator holds them."""
    from ..playbook.wiring import build_rule_evaluator

    rules = build_rule_evaluator(cfg, root)
    return Book3Evaluators(rules.finder, rules.builder, rules.allocator, rules.real)


def build_book3_decider(cfg: dict, root: Path = ROOT):
    from ..books.book1_inputs import LiveBook1Inputs
    from ..books.book1_wiring import cutoff_features, run_context
    from ..books.registered_components import RegisteredComponents
    from ..books.version_registry import VersionRegistry
    from ..books.versions import VERSIONS_FILE
    from ..checks.wiring import build_trade_validator
    from ..constants import RISK_PROFILE_BOOKS
    from ..playbook.decision_run import DecisionRun
    from ..playbook.decision_store import DecisionStore
    from ..research_engine.implied_vol import Black76
    from ..research_engine.ledger import Git
    from ..risk.profile_settings import profile_settings
    from ..storage.wiring import build_quote_store
    from .decider import Book3Decider
    from .proposals import Book3Proposer
    from .strategies import Book3Strategies
    from .wiring import build_strategy_registry

    root = Path(root)
    registered = RegisteredComponents(VersionRegistry(root / VERSIONS_FILE))
    constitutions = ConstitutionFiles(root)
    in_force = lambda day: constitutions.by_sha256().get(registered(BOOK3_AI, day).get(COMPONENT, ""))  # noqa: E731
    inputs = LiveBook1Inputs(root, build_quote_store(), cfg["risk_free_rate"], Black76(),
                             lambda day, snapshot: cutoff_features(cfg, day, snapshot), lambda m: _parts(root, m),
                             lambda day, hashes: run_context(root, day, hashes, BOOK3_AI), BOOK3_AI)  # fmt: skip
    registry = build_strategy_registry(root)
    cap = profile_settings(cfg, RISK_PROFILE_BOOKS).max_loss_per_trade_rs
    validator = build_trade_validator(cfg, BOOK3_AI, root)
    runs = lambda evaluator, picks: DecisionRun(evaluator, DecisionStore(root, BOOK3_AI), validator, picks)  # noqa: E731
    served = lambda day: {COMPONENT: registered(BOOK3_AI, day).get(COMPONENT, ""),  # noqa: E731
                          PROMPT_COMPONENT: prompt_sha256(root)}  # fmt: skip
    prompt_version = f"book3_decide_v1:{prompt_sha256(root)[:12]}"
    return Book3Decider(root, inputs, Book3Strategies(registry), build_book3_evaluators(cfg, root),
                        Book3Proposer(registry, in_force, cap, lambda: playbook_rules(root)), runs, Git(root).head,
                        served, lambda name, version: playbook_widths(root, name, version), prompt_version)  # fmt: skip


def build_book3_orders(cfg: dict, root: Path = ROOT):
    """Book 3's `OrderBuilder`: the replay with C4's validator as the run used it, writing nothing (judge 84)."""
    from ..checks.wiring import build_trade_validator
    from ..playbook.wiring import build_code_tree
    from .orders import Book3Orders

    validator = build_trade_validator(cfg, BOOK3_AI, root, log=False)
    return Book3Orders(build_book3_evaluators(cfg, root), build_code_tree(root), validator)


def build_book3_exit_rules(root: Path = ROOT, alerts=None):
    """Book 1's exit rules over Book 3's records: each trade's time exit as its run read the spec; today's spec file
    only feeds the alerts."""
    from ..books.account import PaperAccount
    from ..books.book1_exits import PlaybookExitRules
    from ..books.book1_records import decided_exit_days
    from ..composition import build_alert_sender, build_session_calendar
    from ..desk.records import DeskRecords
    from ..playbook.opportunities import OpportunityFinder
    from ..research_engine.cycles import TradingDays
    from .registry import spec_path

    finder = OpportunityFinder(TradingDays(build_session_calendar()))

    def spec_text(version: str) -> str | None:
        path = Path(root) / spec_path(version)
        return path.read_text(encoding="utf-8") if path.is_file() else None

    records = lambda book: DeskRecords(PaperAccount(root, book))  # noqa: E731
    return PlaybookExitRules(lambda book: decided_exit_days(root, book, finder), spec_text, records,
                             alerts or build_alert_sender())  # fmt: skip


def build_book3_shadow_reader(cfg: dict, root: Path = ROOT):
    from ..desk.common_pack import CommonPack
    from ..desk.pack_store import PackStore
    from ..desk.timetable import timetable_from_config
    from ..playbook.history import PlaybookGit
    from .shadow_reader import Book3ShadowReader

    packs, timetable = PackStore(root), timetable_from_config(cfg)

    def common(day: date):
        path = packs.common_path(day)
        return CommonPack.read(day, path) if path.is_file() else None

    return Book3ShadowReader(root, PlaybookGit(root), common,
                             lambda day: timetable.at(day, timetable.execution_snapshot))  # fmt: skip


def playbook_rules(root: Path = ROOT) -> dict[str, str]:
    """Each playbook version's rule key -> its version ID (D1's files as they stand)."""
    from ..playbook.documents import strategy_from_text
    from ..playbook.schema import rule_sha256

    folder = Path(root) / PLAYBOOK_FOLDER
    return {rule_sha256(strategy_from_text(p.read_text(encoding="utf-8"), p.name)): p.stem
            for p in sorted(folder.glob("*.yaml"))}  # fmt: skip


def playbook_widths(root: Path, name: str, version: int):
    """A common opportunity's version widths, from its playbook file (None when it cannot be read)."""
    from ..playbook.documents import strategy_from_text
    from ..playbook.fields import PlaybookError
    from ..playbook.schema import file_name

    path = Path(root) / PLAYBOOK_FOLDER / file_name(name, version)
    try:
        return strategy_from_text(path.read_text(encoding="utf-8"), path.name).structure.widths
    except (OSError, PlaybookError):
        return None


def _parts(root: Path, market) -> tuple:
    """Book 3's own account for C2 and its trade counts; it has no shadow candidates, so no shadow books."""
    from ..books.account import PaperAccount
    from ..books.book1_records import recorded_terms
    from ..desk.records import DeskRecords
    from ..desk.trade_counts import DeskTradeCounts
    from ..risk.book_view import load_risk_book
    from .no_shadows import NoShadowBooks

    terms = recorded_terms(root, BOOK3_AI)
    counts = DeskTradeCounts(DeskRecords(PaperAccount(root, BOOK3_AI)))
    return load_risk_book(root, BOOK3_AI, market, terms), counts, NoShadowBooks()
