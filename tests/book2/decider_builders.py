"""Fixtures for story F5's decider: Book 2's view of a test playbook (a registered research candidate, SC widths
200/100/50 and one lot, built at 100; a paper version, the same widths and two lots, built at 50 x 2), each with a
real envelope file registered in D6 under the test root, C4's app checker in Book 2's `EnvelopeMode`, Book 2's own
account, and F1t's accepted answer."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path

import yaml

from fno.book2.decider import Book2Decider
from fno.book2.evaluation import Book2Evaluators
from fno.book2.sheet import Book2Sheet
from fno.book2.validator import Book2TradeValidator
from fno.book3.no_shadows import NoShadowBooks
from fno.books.book1 import Book1Day, Book1Inputs
from fno.books.version_registry import VersionRegistry, VersionRow
from fno.books.versions import VERSIONS_FILE
from fno.constants import BOOK2_HYBRID
from fno.desk.common_pack import CommonPack
from fno.playbook.decision_run import DecisionRun
from fno.playbook.decision_store import DecisionStore
from fno.playbook.envelope_files import EnvelopeFiles, component_key
from tests.book3.engine_builders import COMMON_SHA, CONTEXT, PRIVATE_SHA, Accepted, Pack, validator
from tests.decisions.builders import doc, snapshot
from tests.playbook.builders import DOCUMENT
from tests.playbook.evaluation_builders import DAY, EXPIRY, Counts, FixedValues, chain_market, evaluator
from tests.risk.builders import book

RESEARCH = doc("sc-r", "research", expected="none", structure={**DOCUMENT["structure"], "widths": [200, 100, 50]})
PAPER = doc("sc-p", structure={**DOCUMENT["structure"], "widths": [200, 100, 50], "lots": 2})  # built: 50 x 2 lots
DOCS = (RESEARCH, PAPER)
R, P = f"sc-r-v1:{EXPIRY.isoformat()}", f"sc-p-v1:{EXPIRY.isoformat()}"
ALL_ALLOWED = dict.fromkeys(("follow_rule", "choose_strategy", "no_trade", "choose_width", "reduce_lots"), "allowed")


def repository(root: Path, docs=DOCS, actions=None) -> Path:
    """Each version's envelope file (all five actions allowed unless `actions` says otherwise), registered in D6."""
    folder = root / "playbook" / "envelopes"
    folder.mkdir(parents=True, exist_ok=True)
    for d in docs:
        text = yaml.safe_dump({"playbook": d["name"], "version": d["version"], "actions": actions or ALL_ALLOWED})
        (folder / f"{d['name']}-v{d['version']}.yaml").write_text(text, encoding="utf-8")
    components = {component_key(k): e.sha256 for k, e in EnvelopeFiles(root).all().items()}
    VersionRegistry(root / VERSIONS_FILE).append(
        VersionRow(BOOK2_HYBRID, "1", date(2026, 10, 1), "c" * 40, components, "test"))  # fmt: skip
    return root


class FixedInputs(Book1Inputs):
    def __init__(self, counts=None, values=None, context=None):
        self.counts, self.values, self.context = counts or Counts(), values, context or CONTEXT

    def day(self, day):
        return Book1Day(chain_market(), FixedValues(self.values), book(name=BOOK2_HYBRID), self.counts, NoShadowBooks(),
                        self.context)  # fmt: skip


def evaluators() -> Book2Evaluators:
    rules = evaluator()
    return Book2Evaluators(rules.finder, rules.builder, rules.allocator, rules.real)


def the_snapshot(docs=DOCS):
    return snapshot(*docs, registered_research=tuple(d["name"] for d in docs if d["status"] == "research"))


def decider(root: Path, docs=DOCS, paused=(), inputs=None, runs=None) -> Book2Decider:
    def default_runs(evaluator_, picks, paired, counts, rule_defaults):
        checked = Book2TradeValidator(validator(root, log=True, book=BOOK2_HYBRID), paired, counts)
        return DecisionRun(evaluator_, DecisionStore(root, BOOK2_HYBRID), checked, picks, rule_defaults)

    served = lambda day: {"book2_prompt": "p" * 64}  # noqa: E731
    return Book2Decider(root, inputs or FixedInputs(), lambda: the_snapshot(docs), lambda day: paused, evaluators(),
                        runs or default_runs, EnvelopeFiles(root).all, served)  # fmt: skip


def sheet_for(docs=DOCS, paused=(), inputs=None) -> dict:
    """The day sheet as the pack step builds it (the same code the decider re-runs)."""
    the_inputs = inputs or FixedInputs()
    sheet = Book2Sheet(evaluators(), lambda: the_snapshot(docs), lambda day: paused,
                       lambda day, common: the_inputs.day(day))  # fmt: skip
    return dict(sheet.sheet(BOOK2_HYBRID, DAY, CommonPack(DAY, {})))


def slot(default, action="follow_rule", opportunity_id=None, width=None, lots=None, reason="as the rule says"):
    return {"default": default, "action": action, "opportunity_id": opportunity_id, "width": width, "lots": lots,
            "reason": reason}  # fmt: skip


def decision(slots, reason="the desk's reason", evidence=()) -> dict:
    actions = {s["action"] for s in slots}
    action = (
        "follow_rule" if actions <= {"follow_rule"} else "trade" if actions & {"trade", "follow_rule"} else "no_trade"
    )
    return {"action": action, "reason": reason, "slots": list(slots), "evidence": list(evidence)}


def accepted(the_decision: dict, sheet: dict | None = None, **changes) -> Accepted:
    body = {"evaluation": sheet if sheet is not None else sheet_for()}
    base = Accepted(the_decision, Pack(PRIVATE_SHA, body), book=BOOK2_HYBRID, version="book2_hybrid-decision-v1",
                    common_pack=Pack(COMMON_SHA, {"opportunities": []}))  # fmt: skip
    return replace(base, **changes)
