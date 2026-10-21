"""Story D5 fixtures: a temporary git repository, a constitution file, Book 3 specs in D1's playbook format, and a
registry on a fixed clock."""

from __future__ import annotations

import subprocess
from datetime import date

import yaml

from fno.book3.constitution import parse_constitution
from fno.book3.registry import Provenance, StrategyRegistry
from fno.research_engine.ledger import Git, Ledger
from tests.playbook.builders import document

CONSTITUTION = {"version": 1, "underlying": "NIFTY", "expiry": "monthly",
                "structures": ["LC", "LP", "CDS", "CCS", "PDS", "PCS", "SF", "SC", "BF"], "max_holding_days": 21,
                "sources": ["common_pack", "private_pack"], "risk": "risk.profiles.books",
                "scoring": "research/evaluation/PROTOCOL.md"}  # fmt: skip
PROVENANCE = Provenance("model-x", "prompt-v1", "roles-v1", "new")


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def init_repo(root):
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.invalid")
    git(root, "config", "user.name", "test")
    (root / "README").write_text("x\n")
    (root / "research").mkdir()  # the research ledger's folder, as in the repository
    return commit(root, "start")


def commit(root, message):
    git(root, "add", ".")
    git(root, "commit", "-qm", message)
    return git(root, "rev-parse", "HEAD")


def constitution_bytes(**changes) -> bytes:
    return yaml.safe_dump({**CONSTITUTION, **changes}, sort_keys=False).encode()


def constitution(**changes):
    return parse_constitution(constitution_bytes(**changes), "test")


def spec_text(name="b3-sc", code="SC", max_days=40, exit_days=21, kind="monthly", version=1, min_days=30) -> str:
    doc = document(name=name, status="research")
    doc["version"] = version
    doc["structure"] = dict(doc["structure"], code=code)
    doc["structure"]["expiry"] = dict(doc["structure"]["expiry"], kind=kind, min_days=min_days, max_days=max_days,
                                      exit_days_before_expiry=exit_days)  # fmt: skip
    return yaml.safe_dump(doc, sort_keys=False)


def registry(root, today=date(2026, 11, 2)) -> StrategyRegistry:
    return StrategyRegistry(root, Git(root), Ledger(root), lambda: today)
