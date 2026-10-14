"""Scoreboard B's adapters (story S2): the book's operating-cost file in C1's columns, the AI cost until F8 exists,
each day's marks from the execution snapshot E3 recorded, and the SHA-256 of every file the board reads."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path

from ..accounting.ledgers import read_operating_costs
from ..books.paths import account_folder, book_folder
from ..books.versions import VERSIONS_FILE
from ..constants import BOOK1_RULES, JOURNAL_FOLDER
from ..desk.run_log import RUNS_FOLDER
from ..desk.snapshot import ContractKey, ExecutionSnapshotSource
from ..playbook.decision_store import DecisionStore
from ..scorecard.scorecard import snapshot_marks
from .committed_runs import DayRun

OPERATING_COSTS_FILE = "operating_costs.csv"


class FileOperatingCosts:
    """`journal/<book>/operating_costs.csv`, C1's columns; no file means none recorded."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def path(self, book: str) -> Path:
        return book_folder(self.root, book) / OPERATING_COSTS_FILE

    def rows(self, book: str) -> list[dict]:
        path = self.path(book)
        return read_operating_costs(path.read_text(encoding="utf-8")) if path.is_file() else []


class AiCostBeforeF8:
    """Book 1 runs no AI, so its allocated AI cost is a true zero; the AI books' cost is unknown until F8."""

    def allocated(self, book: str, first: date, last: date) -> float | None:
        return 0.0 if book == BOOK1_RULES else None


class SnapshotMarks:
    """A day's marks: the mid of every valid quote in the execution snapshot E3 recorded as valid that day; none on a
    day without one (the daily values then carry the last valid mark, flagged stale)."""

    def __init__(self, snapshots: ExecutionSnapshotSource, ids: Mapping[date, str]):
        self.snapshots, self.ids = snapshots, dict(ids)
        self._marks: dict[date, Mapping[ContractKey, float]] = {}

    def __call__(self, day: date) -> Mapping[ContractKey, float]:
        if day not in self.ids:
            return {}
        if day not in self._marks:
            self._marks[day] = snapshot_marks(self.snapshots.snapshot(day, self.ids[day]))
        return self._marks[day]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_hashes(root: Path, books: Sequence[str], runs: Sequence[DayRun]) -> dict[str, str]:
    """Every record file the board reads, by repository path (dot files and temporary files aside); the quote
    snapshots are named by the run logs, which are hashed here."""
    root = Path(root)
    folders = [root / JOURNAL_FOLDER / RUNS_FOLDER, *(account_folder(root, b) for b in books)]
    folders += [DecisionStore(root, r.book).day_folder(r.day) / r.run_id for r in runs]
    paths = [p for folder in folders if folder.is_dir() for p in folder.iterdir() if p.is_file()]
    paths += [root / VERSIONS_FILE, *(book_folder(root, b) / OPERATING_COSTS_FILE for b in books)]
    kept = sorted({p for p in paths if p.is_file() and not p.name.startswith(".") and not p.name.endswith(".tmp")})
    return {p.relative_to(root).as_posix(): _sha256(p) for p in kept}
