"""Fixtures for story D3: a playbook snapshot from playbook documents, and a decision run over D2's test evaluator."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import yaml

from fno.playbook.decision_inputs import PlaybookSnapshot
from fno.playbook.decision_run import DecisionRun
from fno.playbook.decision_store import DecisionStore
from fno.playbook.registry import RegistryRow, render
from fno.playbook.schema import parse_strategy
from tests.playbook.builders import document
from tests.playbook.evaluation_builders import (
    DAY,
    Counts,
    FixedValues,
    OwnShadowBooks,
    chain_market,
    evaluator,
)  # fmt: skip
from tests.risk.builders import book

COMMIT = "c" * 40
CONTEXT = {
    "code_commit": COMMIT, "config_sha256": "f" * 64, "version_id": "book1-v1", "common_pack_sha256": "a" * 64,
    "private_pack_sha256": "b" * 64, "authority_check": None, "strategy_id": None, "strategy_spec_sha256": None,
    "model_served": None, "session_id": None, "judge": None, "owner_override": None, "forecasts": None,
}  # fmt: skip


def doc(name: str, status: str = "paper", expected: float | str = 150.0, **changes) -> dict:
    result = document(name=name, status=status, **changes)
    result["evaluation_plan"]["expected_net_per_opportunity"] = expected
    return result


def snapshot(*docs: dict, registered_research: tuple[str, ...] = ()) -> PlaybookSnapshot:
    """Each paper document approved the week before DAY; research ones registered when named."""
    rows = []
    for d in docs:
        if d["status"] != "research" or d["name"] in registered_research:
            sha = parse_strategy(d).parameters_sha256
            evidence = "abcdef1" if d["status"] == "paper" else ""
            rows.append(
                RegistryRow(d["name"], d["version"], sha, d["status"], DAY - timedelta(days=7), "owner", evidence)
            )
    files = {f"{d['name']}-v{d['version']}.yaml": yaml.safe_dump(d, sort_keys=False) for d in docs}
    return PlaybookSnapshot(files, render(rows), COMMIT)


def run_day(root: Path, playbook: PlaybookSnapshot, the_book=None, prices=None, values=None, counts=None) -> Path:
    store = DecisionStore(root, "book1_rules")
    return DecisionRun(evaluator(), store).decide(
        DAY, playbook, chain_market(prices), FixedValues(values), the_book or book(), counts or Counts(),
        OwnShadowBooks(), CONTEXT,
    )  # fmt: skip


class SameCode:
    """The running code is the recorded commit (the real check, GitCodeTree, is tested in test_replay_guard.py)."""

    def matches(self, commit: str) -> bool:
        return True


SAME_CODE = SameCode()
