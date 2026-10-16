"""Stories F6 and F7 fixtures: a temporary git repository with Book 3's constitution, its D6 component and specs
registered by D5 on a fixed clock; D2's test market (DAY 13 Oct 2026, the 27 Nov expiry 45 days away); C4's app
checker in Book 3's mode over the A4 capture of that market; fake accepted answers as F1t hands them over."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import yaml

from fno.book3.constitution import COMPONENT
from fno.book3.decider import Book3Decider
from fno.book3.evaluation import Book3Evaluators, day_sheet
from fno.book3.proposals import Book3Proposer
from fno.book3.registry import Provenance
from fno.book3.strategies import Book3Strategies
from fno.books.book1 import Book1Day, Book1Inputs
from fno.books.version_registry import VersionRegistry, VersionRow
from fno.books.versions import VERSIONS_FILE
from fno.checks.validity import Sources, ValidityChecker
from fno.checks.validity_adapter import BookTradeValidator
from fno.checks.validity_evidence import EvidenceReader
from fno.checks.validity_limits import LimitChecks
from fno.checks.validity_listing import NseListing
from fno.checks.wiring import validity_modes
from fno.composition import DESK_DECISION_TIME
from fno.constants import BOOK3_AI
from fno.playbook.decision_run import DecisionRun
from fno.playbook.decision_store import DecisionStore
from fno.quotes.recorder import DATASET
from fno.research_engine.ledger import Git
from tests.book3.builders import commit, constitution, constitution_bytes, init_repo, registry
from tests.checks.builders import committed_record
from tests.checks.validity_sources import Accounts, limits
from tests.decisions.test_validity_link import MARGINS, NSE, Captures, quote_store
from tests.playbook.builders import DOCUMENT
from tests.playbook.evaluation_builders import DAY, EXPIRY, Counts, FixedValues, OwnShadowBooks, chain_market, evaluator
from tests.risk.builders import ZERO_CHARGES, book

YESTERDAY = DAY - timedelta(days=1)
OPPORTUNITY = f"b3-sc-v1:{EXPIRY.isoformat()}"
PROVENANCE = Provenance("model-x", "prompt-v1", "none", "new")
PROMPT_SHA, CONSTITUTION_SHA = "p" * 64, constitution().sha256
SERVED = {COMPONENT: CONSTITUTION_SHA, "book3_prompt": PROMPT_SHA}
CONTEXT = {"code_commit": "c" * 40, "config_sha256": "f" * 64, "version_id": "book3-v1"}
COMMON_OPPORTUNITIES = [
    {"opportunity_id": f"sc-a-v1:{EXPIRY.isoformat()}", "strategy": "sc-a", "version": 1},
    {"opportunity_id": "no_trade"},
]  # fmt: skip


def spec_document(name="b3-sc", **changes) -> dict:
    """A Book 3 spec in D1's format: SC, widths 300/200/100, one lot, window 30-45 days, exit 25 days before expiry
    (held 20 days), no entry condition, no tested estimate, research status."""
    doc = copy.deepcopy(DOCUMENT)
    doc.update(name=name, status="research", entry_conditions=[])
    doc["structure"]["expiry"] = {"kind": "monthly", "min_days": 30, "max_days": 45, "exit_days_before_expiry": 25}
    doc["exits"] = {**doc["exits"], "time": "25 days to expiry"}
    doc["evaluation_plan"]["expected_net_per_opportunity"] = "none"
    for key, value in changes.items():
        doc[key] = value
    return doc


def spec(name="b3-sc", **changes) -> str:
    return yaml.safe_dump(spec_document(name, **changes), sort_keys=False)


def repository(root: Path, specs=(), on: date = YESTERDAY) -> Path:
    """The constitution, its D6 component, each spec registered on `on`, all committed."""
    root.mkdir(parents=True, exist_ok=True)
    init_repo(root)
    (root / "book3").mkdir()
    (root / "book3" / "constitution-v1.yaml").write_bytes(constitution_bytes())
    VersionRegistry(root / VERSIONS_FILE).append(
        VersionRow(BOOK3_AI, "b3-v1", date(2026, 10, 1), "c" * 40, {COMPONENT: CONSTITUTION_SHA}, "test"))  # fmt: skip
    for text in specs:
        registry(root, today=on).register(text, PROVENANCE, constitution())
    commit(root, "constitution and strategies")
    return root


class FixedInputs(Book1Inputs):
    def __init__(self, the_book=None, values=None):
        self.the_book, self.values = the_book or book(name=BOOK3_AI), values

    def day(self, day):
        return Book1Day(chain_market(), FixedValues(self.values), self.the_book, Counts(), OwnShadowBooks(),
                        CONTEXT)  # fmt: skip


def evaluators() -> Book3Evaluators:
    rules = evaluator()
    return Book3Evaluators(rules.finder, rules.builder, rules.allocator, rules.real)


def validator(root: Path, log: bool = False) -> BookTradeValidator:
    """C4's app checker in Book 3's mode (D5): the constitution, D6 and registry under `root`."""
    store = quote_store()
    sources = Sources(EvidenceReader(store, DATASET), NseListing(NSE), Accounts(None))
    checker = ValidityChecker(sources, LimitChecks(limits(), ZERO_CHARGES, MARGINS), validity_modes(root))
    from fno.checks.validity_failures import ValidityFailureLog

    return BookTradeValidator(BOOK3_AI, checker, Captures(committed_record(store, DAY, "exec")), DESK_DECISION_TIME,
                              ValidityFailureLog(root) if log else None)  # fmt: skip


def widths(name, version):
    return (300.0, 200.0, 100.0) if (name, version) == ("sc-a", 1) else None


def decider(root: Path, today: date = DAY, inputs=None, playbook=None) -> Book3Decider:
    the_registry = registry(root, today=today)
    proposer = Book3Proposer(the_registry, lambda day: constitution(), 10_000, lambda: dict(playbook or {}))
    check = validator(root)
    runs = lambda ev, picks: DecisionRun(ev, DecisionStore(root, BOOK3_AI), check, picks)  # noqa: E731
    return Book3Decider(root, inputs or FixedInputs(), Book3Strategies(the_registry), evaluators(), proposer, runs,
                        Git(root).head, lambda day: SERVED, widths, "book3_decide_v1:test")  # fmt: skip


@dataclass
class Pack:
    sha256: str
    body: dict = field(default_factory=dict)


@dataclass
class Accepted:
    decision: dict
    private_pack: Pack
    day: date = DAY
    registered_model: str = "model-x"
    model_reported: str = "model-x"
    session: str = "https://claude.ai/code/session_test"
    common_pack: Pack = field(default_factory=lambda: Pack("a" * 64, {"opportunities": COMMON_OPPORTUNITIES}))
    analyst_cards: dict | None = None


def decision(trades=(), proposals=(), shadow=(), cards=(), reason="the desk's reason") -> dict:
    return {"action": "trade" if trades else "no_trade", "reason": reason,
            "trades": [{"opportunity_id": t, "reason": f"pick {t}"} for t in trades], "proposals": list(proposals),
            "shadow": list(shadow), "cards_used": list(cards)}  # fmt: skip


def proposal(text: str, supersedes: str = "") -> dict:
    return {"spec": text, "supersedes": supersedes, "reason": "a new idea"}


def sheet_for(root: Path, today: date = DAY) -> dict:
    """The day sheet as the pack step would build it (the same code the decider re-runs)."""
    tradable = Book3Strategies(registry(root, today=today)).on(today, Git(root).head())
    rules, _ = evaluators().with_picks(())
    inputs = FixedInputs().day(today)
    evaluation = rules.evaluate(today, tradable.snapshot.playbook(), inputs.market, inputs.features, inputs.book,
                                inputs.counts, inputs.shadow)  # fmt: skip
    return day_sheet(today, evaluation, tradable.snapshot.commit)


def accepted(root: Path, the_decision: dict, sheet: dict | None = None, **changes) -> Accepted:
    body = {"evaluation": sheet if sheet is not None else sheet_for(root)}
    return Accepted(the_decision, Pack("b" * 64, body), **changes)
