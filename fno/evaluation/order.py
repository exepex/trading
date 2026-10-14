"""When a protocol version applies (story S1, criteria 1 and 3):
- **Freeze order:** the commit that added a version's freeze record must be a strict git ancestor of every book's
  first counted decision. A counted decision is a D3 run dated on or after the common start; earlier runs are pilot
  evidence.
- **Version of a decision:** a decision is counted under the latest protocol version whose freeze record's commit is
  a strict ancestor of the decision's own commit. With no such version it is not counted.
A run's commit is the one that added its `records.sha256` (D3)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..constants import JOURNAL_FOLDER
from ..playbook.decision_store import DECISIONS_FOLDER, SUMS_FILE
from .freeze import freeze_path

FREEZE_NAME = re.compile(r"^FREEZE_v([1-9][0-9]*)\.md$")


@dataclass(frozen=True)
class CountedDecision:
    book: str
    run: str  # repository path of the run folder
    commit: str


def _strictly_before(git, older: str, newer: str) -> bool:
    return older != newer and git.is_ancestor(older, newer)


def freeze_commit(git, version: int) -> str | None:
    added = git.added_in(freeze_path(version))
    return added[0] if added else None


def frozen_versions(root: Path) -> list[int]:
    folder = Path(root) / Path(freeze_path(1)).parent
    names = (FREEZE_NAME.match(p.name) for p in folder.glob("FREEZE_v*.md")) if folder.is_dir() else ()
    return sorted(int(m.group(1)) for m in names if m)


def first_counted_decision(root: Path, git, book: str, common_start: date | None) -> CountedDecision | None:
    """The book's earliest committed run dated on or after the common start (every run when none is given)."""
    folder = Path(root) / JOURNAL_FOLDER / book / DECISIONS_FOLDER
    days = sorted(p for p in folder.iterdir() if p.is_dir()) if folder.is_dir() else []
    for day in days:
        if common_start is not None and date.fromisoformat(day.name) < common_start:
            continue
        for run in sorted(p for p in day.iterdir() if p.is_dir() and not p.name.startswith(".")):
            path = (run / SUMS_FILE).relative_to(root).as_posix()
            added = git.added_in(path)
            if added:
                return CountedDecision(book, run.relative_to(root).as_posix(), added[0])
    return None


def order_problems(git, version: int, firsts: Sequence[CountedDecision]) -> list[str]:
    """Why version `version`'s freeze does not precede each book's first counted decision; empty when it does."""
    frozen = freeze_commit(git, version)
    if frozen is None and firsts:
        return [f"{freeze_path(version)} is not committed, but counted decisions exist"]
    return [
        f"{first.book}: first counted decision {first.run} ({first.commit[:10]}) is not after the v{version} freeze"
        for first in firsts
        if not _strictly_before(git, frozen, first.commit)
    ]


def version_of(root: Path, git, decision_commit: str) -> int | None:
    """The protocol version a decision is counted under; None when no freeze precedes it."""
    for version in reversed(frozen_versions(root)):
        frozen = freeze_commit(git, version)
        if frozen and _strictly_before(git, frozen, decision_commit):
            return version
    return None
