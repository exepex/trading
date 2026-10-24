"""Criterion 8, on the real git history (as judge 480 required for D6): the commit adding CARD_V5V1 with its ledger
and gate-log rows is a strict ancestor of the first commit touching `fno/forecast_v5_v1/`. Plus the same check on a
small repository where the code came first, which it must refuse."""

from __future__ import annotations

import subprocess
from pathlib import Path

from fno.config import ROOT
from tests.history import require_full_history

CARD = "research/ideas/CARD_V5V1.md"
ROWS = ("research/ledger.csv", "research/factory/gates.csv")
PACKAGE = "fno/forecast_v5_v1"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def registered_first(repo: Path) -> bool:
    """The card's adding commit carries both rows and strictly precedes every commit touching the package."""
    card = git(repo, "log", "--diff-filter=A", "--format=%H", "--", CARD).splitlines()
    code = git(repo, "log", "--reverse", "--format=%H", "--", PACKAGE).splitlines()
    if len(card) != 1 or not code:
        return False
    if not set(ROWS) <= set(git(repo, "show", "--name-only", "--format=", card[0]).splitlines()):
        return False
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", card[0], code[0]], cwd=repo, check=False)
    return ancestor.returncode == 0 and card[0] != code[0]


def test_the_card_and_its_rows_came_before_any_code():
    require_full_history(ROOT)
    assert registered_first(ROOT)


def _commit(repo: Path, *names: str) -> None:
    for name in names:
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(name)
    git(repo, "add", *names)
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", names[0])


def test_code_before_the_card_is_refused(tmp_path):
    git(tmp_path, "init", "-q")
    _commit(tmp_path, f"{PACKAGE}/history.py")
    _commit(tmp_path, CARD, *ROWS)
    assert not registered_first(tmp_path)


def test_a_card_without_its_rows_is_refused(tmp_path):
    git(tmp_path, "init", "-q")
    _commit(tmp_path, CARD)
    _commit(tmp_path, f"{PACKAGE}/history.py")
    assert not registered_first(tmp_path)


def test_the_card_and_rows_then_code_passes(tmp_path):
    git(tmp_path, "init", "-q")
    _commit(tmp_path, CARD, *ROWS)
    _commit(tmp_path, f"{PACKAGE}/history.py")
    assert registered_first(tmp_path)
