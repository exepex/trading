"""Composition root of Book 2's decisions (story F5): its day sheet (the pack step), its decider (F1t's port), its
orders and exits (E3's seams, dispatched per book by the daily run) and its research pauses (E6's reviews). D2's
evaluator parts, C2, C4's validator, D4's envelopes, D6's components, Book 1's input reader and exit rules, and Book
3's account parts are reused as built; swapping any of them changes this file only."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ..config import ROOT
from ..constants import BOOK2_HYBRID
from .evaluation import Book2Evaluators
from .pauses import PAUSES_FILE, ResearchPauses

PROMPT_FILE = "agents/book2/decide_v1.md"
PROMPT_COMPONENT = "book2_prompt"


def prompt_sha256(root: Path = ROOT) -> str:
    return hashlib.sha256((Path(root) / PROMPT_FILE).read_bytes()).hexdigest()


def build_book2_evaluators(cfg: dict, root: Path = ROOT) -> Book2Evaluators:
    """D2's own finder, candidate builder, allocator (C2) and real-book check, as Book 1's evaluator holds them."""
    from ..playbook.wiring import build_rule_evaluator

    rules = build_rule_evaluator(cfg, root)
    return Book2Evaluators(rules.finder, rules.builder, rules.allocator, rules.real)


def build_research_pauses(root: Path = ROOT) -> ResearchPauses:
    from ..research_engine.ledger import Git

    def history() -> list[str]:
        git = Git(root)
        return [git.committed_text(PAUSES_FILE, commit) or "" for commit in git.commits_touching(PAUSES_FILE)]

    return ResearchPauses(root, history)


def build_book2_inputs(cfg: dict, root: Path = ROOT):
    """Book 1's input reader on Book 2's own account."""
    from ..book3.decision_wiring import account_parts
    from ..books.book1_inputs import LiveBook1Inputs
    from ..books.book1_wiring import cutoff_features, run_context
    from ..research_engine.implied_vol import Black76
    from ..storage.wiring import build_quote_store

    return LiveBook1Inputs(root, build_quote_store(), cfg["risk_free_rate"], Black76(),
                           lambda day, snapshot: cutoff_features(cfg, day, snapshot),
                           lambda market: account_parts(root, market, BOOK2_HYBRID),
                           lambda day, hashes: run_context(root, day, hashes, BOOK2_HYBRID), BOOK2_HYBRID)  # fmt: skip


def build_book2_sheet(cfg: dict, root: Path = ROOT):
    """Book 2's `BookSheet` for the pack step: the decider's own evaluators, playbook view and inputs."""
    from ..playbook.wiring import snapshot_playbook
    from .sheet import Book2Sheet

    root, inputs = Path(root), build_book2_inputs(cfg, root)
    at_cutoff = lambda day, common: inputs.at_cutoff(day, common, {})  # noqa: E731 - the pack's hashes come later
    return Book2Sheet(build_book2_evaluators(cfg, root), lambda: snapshot_playbook(root),
                      build_research_pauses(root).paused_on, at_cutoff)  # fmt: skip


def build_book2_decider(cfg: dict, root: Path = ROOT):
    from ..checks.wiring import build_trade_validator
    from ..playbook.decision_run import DecisionRun
    from ..playbook.decision_store import DecisionStore
    from ..playbook.envelope_files import EnvelopeFiles
    from ..playbook.wiring import snapshot_playbook
    from .decider import Book2Decider
    from .validator import Book2TradeValidator

    root = Path(root)
    base = build_trade_validator(cfg, BOOK2_HYBRID, root)

    def runs(evaluator, picks, paired, counts, rule_defaults):
        validator = Book2TradeValidator(base, paired, counts)
        return DecisionRun(evaluator, DecisionStore(root, BOOK2_HYBRID), validator, picks, rule_defaults)

    served = lambda day: {PROMPT_COMPONENT: prompt_sha256(root)}  # noqa: E731
    return Book2Decider(root, build_book2_inputs(cfg, root), lambda: snapshot_playbook(root),
                        build_research_pauses(root).paused_on, build_book2_evaluators(cfg, root), runs,
                        EnvelopeFiles(root).all, served)  # fmt: skip


def build_book2_orders(cfg: dict, root: Path = ROOT):
    """Book 2's `OrderBuilder`: the replay with C4's validator as the run used it, writing nothing (judge 84)."""
    from ..checks.wiring import build_trade_validator
    from ..playbook.wiring import build_code_tree
    from .orders import Book2Orders

    validator = lambda: build_trade_validator(cfg, BOOK2_HYBRID, root, log=False)  # noqa: E731
    return Book2Orders(build_book2_evaluators(cfg, root), build_code_tree(root), validator)


def build_book2_exit_rules(root: Path = ROOT, alerts=None):
    """Book 1's exit rules, read for Book 2's records: each trade's time exit as its run read the version file."""
    from ..books.book1_wiring import build_book1_exit_rules

    return build_book1_exit_rules(root, alerts)


def build_book2_pauses_review(cfg: dict, root: Path = ROOT, alerts=None):
    """Book 2's research pauses as one more review in E6's `reviews` step, on Book 2's own records only."""
    from ..books.account import PaperAccount
    from ..composition import build_alert_sender
    from ..desk.records import DeskRecords
    from ..playbook.wiring import snapshot_playbook
    from ..scorecard.strategy_record import strategy_records
    from .pauses import Book2ResearchPauses

    records = lambda: strategy_records(BOOK2_HYBRID, DeskRecords(PaperAccount(root, BOOK2_HYBRID)), cfg["charges"])  # noqa: E731
    return Book2ResearchPauses(records, lambda: snapshot_playbook(root).playbook(), build_research_pauses(root),
                               alerts or build_alert_sender())  # fmt: skip
