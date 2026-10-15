"""Composition root of Book 1 (story E5): its decider (D2 through D3's decision run, on the two packs, the canonical
snapshot, B7's live features and Book 1's own account) and the two parts E3's daily run takes from it, the orders
(replayed decisions) and the exit rules (playbook time exits). Nothing here reaches a model or a broker."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from datetime import date
from pathlib import Path

from ..config import ROOT
from ..constants import BOOK1_RULES
from .book1 import Book1
from .book1_exits import PlaybookExitRules
from .book1_orders import ReplayedOrders
from .book1_records import recorded_terms


def build_book1(cfg: dict, root: Path = ROOT) -> Book1:
    from ..composition import build_session_calendar
    from ..desk.git_sync import Git, GitCommitter
    from ..playbook.wiring import build_decision_run, snapshot_playbook
    from ..research_engine.implied_vol import Black76
    from ..storage.wiring import build_quote_store
    from .book1_inputs import LiveBook1Inputs

    inputs = LiveBook1Inputs(root, build_quote_store(), cfg["risk_free_rate"], Black76(),
                             lambda day, snapshot: _features(cfg, day, snapshot), lambda market: _parts(root, market),
                             lambda day, hashes: _context(root, day, hashes))  # fmt: skip
    return Book1(root, build_session_calendar(), lambda: snapshot_playbook(root), inputs,
                 build_decision_run(cfg, BOOK1_RULES, root), GitCommitter(Git(root)))  # fmt: skip


def build_book1_orders(cfg: dict, root: Path = ROOT) -> ReplayedOrders:
    """D2's evaluator and C4's validator as Book 1's decision run used them, so the replay reproduces every record."""
    from ..checks.wiring import build_trade_validator
    from ..playbook.wiring import build_code_tree, build_rule_evaluator

    validator = build_trade_validator(cfg, BOOK1_RULES, root, log=False)  # a replay writes nothing (judge 84)
    return ReplayedOrders(build_rule_evaluator(cfg, root), build_code_tree(root), validator)


def build_book1_exit_rules(root: Path = ROOT) -> PlaybookExitRules:
    """Exits fixed at each decision (the committed runs); today's version files only feed the alerts."""
    from ..books.account import PaperAccount
    from ..composition import build_alert_sender, build_session_calendar
    from ..constants import PLAYBOOK_FOLDER
    from ..desk.records import DeskRecords
    from ..playbook.history import PlaybookGit
    from ..playbook.opportunities import OpportunityFinder
    from ..research_engine.cycles import TradingDays
    from .book1_records import decided_exit_days

    finder = OpportunityFinder(TradingDays(build_session_calendar()))

    def version_text(version: str) -> str | None:
        path = root / PLAYBOOK_FOLDER / f"{version}.yaml"
        return path.read_text(encoding="utf-8") if path.is_file() else None

    sums_at = PlaybookGit(root).committed_bytes
    return PlaybookExitRules(lambda book: decided_exit_days(root, book, finder, sums_at), version_text,
                             lambda book: DeskRecords(PaperAccount(root, book)), build_alert_sender())  # fmt: skip


def _features(cfg: dict, day: date, snapshot):
    from ..composition import load_research_data
    from ..playbook.wiring import build_live_feature_values
    from ..research_engine.cycles import cycle_rows
    from ..research_engine.features import ResearchData

    data = load_research_data(range(day.year - 1, day.year + 1), keep=cycle_rows)
    return build_live_feature_values(cfg, ResearchData(data.panel, data.events, {day: snapshot}))


def _parts(root: Path, market) -> tuple:
    from ..books.account import PaperAccount
    from ..desk.records import DeskRecords
    from ..desk.trade_counts import DeskTradeCounts
    from ..desk.wiring import build_shadow_books
    from ..playbook.history import PlaybookGit
    from ..risk.book_view import load_risk_book

    terms = recorded_terms(root, BOOK1_RULES, PlaybookGit(root).committed_bytes)
    counts = DeskTradeCounts(DeskRecords(PaperAccount(root, BOOK1_RULES)))
    return load_risk_book(root, BOOK1_RULES, market, terms), counts, build_shadow_books(market, terms, root)


def _context(root: Path, day: date, hashes: Mapping[str, str]) -> dict:
    """D3's run context for Book 1: the code and config it runs, its D6 version and the packs it read; the AI books'
    fields stay null (D3's schema allows it for Book 1)."""
    from ..books.versions import Versions
    from ..composition import build_version_registry
    from ..playbook.history import PlaybookGit

    git = PlaybookGit(root)
    active = Versions(build_version_registry(root).rows(), git).active_version(BOOK1_RULES, day)
    config = hashlib.sha256((root / "config.yaml").read_bytes()).hexdigest()
    return {"code_commit": git.head(), "config_sha256": config, "version_id": active.version_id if active else None,
            **hashes}  # fmt: skip
