"""Promotion (story F1t): an accepted answer goes to its book's decider, and the run it writes is checked before
anything is committed. A refusal, any exception from the decider, or a failed check restores the decider's write
paths to their state just before `decide()` (`WriteSnapshot`), records what was restored, and leaves the book with no
run for the day, so E3 records no decision and nothing fills. A good run's files are returned for the step's commit."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from ..playbook.decision_store import SUMS_FILE
from .ports import AcceptedDecision, AiBookDecider, DecidedRun, DecisionRefused
from .run_check import run_problems
from .write_snapshot import GitWorktree, OutsideSnapshot, Worktree, WriteSnapshot

NO_DECIDER = "no decider is wired for {book} (its story, F5 or F6, has not landed)"
CHECK_FAILED = "the decided run failed F1t's check: {problems}"
UNDECLARED = "wrote files it did not return (never committed, put back): {paths}"


@dataclass(frozen=True)
class Promotion:
    promoted: bool
    reason: str = ""
    run_id: str = ""
    paths: tuple[Path, ...] = field(default=())  # what the step commits (the run and the decider's other files)
    restored: tuple[str, ...] = field(default=())  # what the restore put back (refusals only)
    refused_run: dict = field(default_factory=dict)  # file -> SHA-256 of a run that failed the check (evidence)


class Promoter:
    def __init__(self, root: Path, deciders: Mapping[str, AiBookDecider], worktree: Worktree | None = None):
        self.root, self.deciders = Path(root), dict(deciders)
        self.worktree = worktree or GitWorktree(root)

    def promote(self, accepted: AcceptedDecision, write_paths: tuple[str, ...]) -> Promotion:
        decider = self.deciders.get(accepted.book)
        if decider is None:
            return Promotion(False, NO_DECIDER.format(book=accepted.book))
        inside = WriteSnapshot.take(self.root, write_paths)
        outside = OutsideSnapshot.take(self.root, self.worktree, write_paths)

        def refused(reason: str, evidence: dict | None = None) -> Promotion:
            restored = tuple(sorted(set(inside.restore()) | set(outside.restore())))
            return Promotion(False, reason, restored=restored, refused_run=evidence or {})

        try:
            decided = decider.decide(accepted)
        except DecisionRefused as refusal:
            return refused(f"the decider refused: {refusal}")
        except Exception as failure:  # noqa: BLE001 - any decider failure is one refused book-day, never a lost run
            return refused(f"the decider failed: {type(failure).__name__}: {failure}")
        problems = run_problems(self.root, decided, accepted, write_paths)
        undeclared = self._undeclared(decided, inside, outside)
        problems += [UNDECLARED.format(paths=", ".join(undeclared))] if undeclared else []
        if problems:
            return refused(CHECK_FAILED.format(problems="; ".join(problems)), _sums(decided.run))
        return Promotion(True, run_id=decided.run.name, paths=(decided.run, *decided.files))

    def _undeclared(self, decided: DecidedRun, inside: WriteSnapshot, outside: OutsideSnapshot) -> list[str]:
        """Every change the decider made that is neither its run nor a file it returned."""
        run = decided.run.resolve()
        declared = {Path(f).resolve() for f in decided.files}
        changes = {c: (self.root / c).resolve() for c in set(inside.changed()) | set(outside.changed())}
        return sorted(c for c, path in changes.items() if not path.is_relative_to(run) and path not in declared)


def _sums(run: Path) -> dict:
    sums = Path(run) / SUMS_FILE
    if not sums.is_file():
        return {}
    return {name: digest for digest, name in (line.split("  ", 1) for line in sums.read_text("utf-8").splitlines())}
