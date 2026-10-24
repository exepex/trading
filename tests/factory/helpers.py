"""Shared test helpers for the factory (story R1): a temporary git repository with a two-trial ledger and a card."""

import subprocess
from pathlib import Path

from fno.research_engine.ledger import Ledger

CARD = "research/ideas/X1.md"
BLOCK = """id: X1
version: 1
trial: 3
experiment: x1-test
description: "X1: a planted idea"
question: planted-question
hypothesis: yes
measurement: no
"""


CLAIMS_FILE = "numbers/ledger-trial.csv"  # story O12e: every test trial id sits in a block claimed for its experiment
CLAIMS = (
    "number,name,session,claimed_at_utc\n1-2,old,session_test,2026-10-25T00:00:00Z\n"
    "3-99,x1-test,session_test,2026-10-25T00:00:00Z\n"
)


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def commit(root, message="commit"):
    git(root, "add", ".")
    git(root, "commit", "-qm", message)
    return git(root, "rev-parse", "HEAD")


def init_repo(root: Path) -> Path:
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.invalid")
    git(root, "config", "user.name", "test")
    ledger = Ledger(root)
    (root / "research").mkdir()
    (root / "numbers").mkdir()
    (root / CLAIMS_FILE).write_text(CLAIMS, encoding="utf-8")
    for trial in ("1", "2"):
        ledger.register(trial, "old", f"trial {trial}", "prospective", True, today=None)
    commit(root, "ledger")
    return root


def write_card(root: Path, block: str = BLOCK, path: str = CARD) -> str:
    card = Path(root) / path
    card.parent.mkdir(parents=True, exist_ok=True)
    card.write_text(f"# Idea card\n\n| Field | Value |\n|---|---|\n\n```factory\n{block}```\n\n## G1\n")
    return path


REGISTER = """## Register

| Data set | Price type | Period | Status | Used by (ledger trials) | Notes |
|---|---|---|---|---|---|
| Quotes | Groww | 2027 | `forward` | none | |
| Closes | NSE | 2019 | `spent` | 1 | |
"""
INPUTS = """gross: {kind: published, least_favourable: 1200, source: a planted study}
tail: {probability: 0.05, loss: 9000, in_gross: no}
cost: {measured: 300, source: a planted measurement}
data_sets: ["Quotes | Groww | 2027"]
measures: planted outcomes
sd_per_trade: 3000
frequency_per_year: 200
pass_level: 0.01
"""
