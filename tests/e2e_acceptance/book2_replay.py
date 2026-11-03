"""Story O11 with F5: the recorded day with Book 2 live beside Book 1. Book 2's private pack carries its day sheet
(the pack step's `Book2Sheet`), a fake AI answer (follow the rule) goes through F1t's real `Promoter` and run check
into Book 2's real decider, C2 and C4's `EnvelopeMode` (the approved version's envelope registered in D6 under the
replay root), and E3's daily run collects, fills and marks Book 2's trade with Book 2's own orders and exits. F1t's
sealing and receipts are its own end-to-end test's (`tests/ai_trading/test_end_to_end.py`); here the answer is
already accepted."""

from __future__ import annotations

import json
from datetime import date

import yaml

from fno.ai_trading.book_dispatch import ExitRulesByBook, OrdersByBook
from fno.ai_trading.ports import AcceptedDecision
from fno.ai_trading.promote import Promoter
from fno.ai_trading.versions import BOOK2_WRITE_PATHS, REGISTRY
from fno.book2.decider import Book2Decider
from fno.book2.evaluation import Book2Evaluators
from fno.book2.orders import Book2Orders
from fno.book2.sheet import Book2Sheet
from fno.book2.validator import Book2TradeValidator
from fno.book3.no_shadows import NoShadowBooks
from fno.books.account import PaperAccount
from fno.books.book1_inputs import LiveBook1Inputs
from fno.books.version_registry import VersionRegistry, VersionRow
from fno.books.versions import VERSIONS_FILE
from fno.checks.wiring import build_trade_validator
from fno.constants import BOOK1_RULES, BOOK2_HYBRID
from fno.desk.common_pack import CommonPack
from fno.desk.pack_store import PackStore
from fno.desk.pack_wiring import build_common_pack_builder, build_private_pack_builder
from fno.desk.packs import WrittenPacks
from fno.desk.private_pack import PrivatePack
from fno.desk.records import DeskRecords
from fno.playbook.decision_run import DecisionRun
from fno.playbook.decision_store import DecisionStore
from fno.playbook.envelope import EnvelopeAction
from fno.playbook.envelope_files import EnvelopeFiles, component_key
from fno.playbook.wiring import build_rule_evaluator
from fno.research_engine.implied_vol import Black76
from tests.book1.builders import Commits
from tests.decisions.builders import SAME_CODE
from tests.playbook.evaluation_builders import Counts, FixedValues
from tests.risk.builders import book

from . import real_day as rd
from .replay import Replay

BOOKS = (BOOK1_RULES, BOOK2_HYBRID)


class AnyBookCommits(Commits):
    """Book 1's test committer, which also finds a run of Book 2 (its `added_in` knows Book 1's folder only)."""

    def added_in(self, path: str):
        for commit, moment, paths, _ in self.made:
            if "/decisions/" in path and any(str(p).endswith(path) for p in paths):
                return commit, moment.isoformat()
        return None


class NoOtherChanges:
    """F1t's worktree port in a root that is no git checkout: the decider's own paths are all that changes."""

    def changed(self) -> set[str]:
        return set()

    def at_head(self, path: str) -> bytes | None:
        return None


class Book2Replay(Replay):
    def __init__(self, root, monkeypatch, alerts, **options):
        super().__init__(root, monkeypatch, alerts, **options)
        self.commits = AnyBookCommits(self.commits.clock)
        register_envelope(root, self.playbook)
        self.packs = WrittenPacks(build_common_pack_builder(root), build_private_pack_builder(root), PackStore(root),
                                  self.packs.cutoff, BOOKS, sheets={BOOK2_HYBRID: self.sheet()},
                                  isolated=(BOOK2_HYBRID,))  # fmt: skip

    def inputs(self) -> LiveBook1Inputs:
        return LiveBook1Inputs(self.root, rd.quote_store(self.root), self.cfg["risk_free_rate"], Black76(),
                               lambda day, snapshot: FixedValues(),
                               lambda market: (book(name=BOOK2_HYBRID), Counts(), NoShadowBooks()),
                               lambda day, hashes: {**self.context, **hashes}, BOOK2_HYBRID)  # fmt: skip

    def evaluators(self) -> Book2Evaluators:
        rules = build_rule_evaluator(self.cfg, self.root)
        return Book2Evaluators(rules.finder, rules.builder, rules.allocator, rules.real)

    def sheet(self) -> Book2Sheet:
        inputs = self.inputs()
        return Book2Sheet(self.evaluators(), lambda: self.playbook, lambda day: (),
                          lambda day, common: inputs.at_cutoff(day, common, {}))  # fmt: skip

    def decider(self) -> Book2Decider:
        base = build_trade_validator(self.cfg, BOOK2_HYBRID, self.root)

        def runs(evaluator, picks, paired, counts, rule_defaults):
            checked = Book2TradeValidator(base, paired, counts)
            return DecisionRun(evaluator, DecisionStore(self.root, BOOK2_HYBRID), checked, picks, rule_defaults)

        return Book2Decider(self.root, self.inputs(), lambda: self.playbook, lambda day: (), self.evaluators(), runs,
                            EnvelopeFiles(self.root).all, lambda day: {"book2_prompt": "p" * 64})  # fmt: skip

    def book2(self, day: date) -> list[str]:
        """O1's `ai_collect` for an answer already accepted: follow the rule on every slot, promoted by F1t."""
        store = PackStore(self.root)
        common = CommonPack.read(day, store.common_path(day))
        private = PrivatePack(BOOK2_HYBRID, day, json.loads(store.private_path(BOOK2_HYBRID, day).read_text()))
        defaults = [d["opportunity_id"] for d in private.body["evaluation"]["rule_default"]]
        slots = [{"default": d, "action": "follow_rule", "opportunity_id": None, "width": None, "lots": None,
                  "reason": "the rule's trade"} for d in defaults]  # fmt: skip
        answer = {"action": "follow_rule", "reason": "follow the rule today", "slots": slots, "evidence": []}
        version = REGISTRY.current(BOOK2_HYBRID)
        accepted = AcceptedDecision(BOOK2_HYBRID, day, version.label, version.registered_model,
                                    version.registered_model, "https://example.invalid/session", common, private,
                                    answer, None, (), "c1", "c2", "journal/ai_decisions/judge.json", False)  # fmt: skip
        promoter = Promoter(self.root, {BOOK2_HYBRID: self.decider()}, NoOtherChanges())
        promotion = promoter.promote(accepted, BOOK2_WRITE_PATHS)
        if not promotion.promoted:
            raise RuntimeError(promotion.reason)
        files = [f for p in promotion.paths for f in ((p.iterdir()) if p.is_dir() else (p,))]
        self.commits.commit(files, f"Book 2 run {promotion.run_id}")
        return [f"book2_hybrid {promotion.run_id} promoted ({promotion.strategy_label or 'no trade'})"]

    def commands(self) -> dict:
        return {**super().commands(), "ai_collect": self.book2}

    def books(self) -> tuple[str, ...]:
        return BOOKS

    def orders(self):
        book1 = super().orders()
        book2 = Book2Orders(self.evaluators(), SAME_CODE,
                            lambda: build_trade_validator(self.cfg, BOOK2_HYBRID, self.root, log=False))  # fmt: skip
        return OrdersByBook({BOOK1_RULES: book1, BOOK2_HYBRID: book2})

    def exit_rules(self):
        rules = super().exit_rules()
        return ExitRulesByBook({BOOK1_RULES: rules, BOOK2_HYBRID: rules})


def register_envelope(root, playbook) -> None:
    """The approved version's envelope (all five actions allowed, as v1) and Book 2's D6 row naming its hash."""
    [strategy] = playbook.playbook().strategies
    folder = root / "playbook" / "envelopes"
    folder.mkdir(parents=True, exist_ok=True)
    actions = dict.fromkeys((a.value for a in EnvelopeAction), "allowed")
    text = yaml.safe_dump({"playbook": strategy.name, "version": strategy.version, "actions": actions})
    (folder / f"{strategy.name}-v{strategy.version}.yaml").write_text(text, encoding="utf-8")
    components = {component_key(k): e.sha256 for k, e in EnvelopeFiles(root).all().items()}
    VersionRegistry(root / VERSIONS_FILE).append(
        VersionRow(BOOK2_HYBRID, "1", rd.ACCOUNTS_START, "c" * 40, components, "replay"))  # fmt: skip


def book2_trades(root) -> list[str]:
    """Book 2's chosen trades on the recorded day, from its D3 records."""
    folder = root / "journal" / BOOK2_HYBRID / "decisions" / rd.DAY.isoformat()
    records = [json.loads(p.read_text()) for p in sorted(folder.glob("*/*.json")) if p.name != "inputs.json"]
    return [r["opportunity_id"] for r in records if r["chosen_action"] == "trade" and r["opportunity_id"] != "no_trade"]


def book2_legs(root) -> list[dict]:
    return DeskRecords(PaperAccount(root, BOOK2_HYBRID)).fill_rows()
