"""The playbook loader (story D1): every `playbook/<name>-v<n>.yaml`, checked against the registry and the approval
checks. Any refusal stops the whole load: the desk never trades from a playbook with one bad file in it. One exception
(judge 67, story E6): a version on paper whose live feature has drifted is not approved, and is listed as drifted for
its automatic pause; the other versions keep loading. An empty playbook is valid and approves nothing, so Book 1 then
trades nothing."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ..constants import PLAYBOOK_REGISTRY_FILE
from .approval_checks import ApprovalCheck, LiveFeatureDrift, run_checks
from .documents import strategy_from_text
from .fields import PlaybookError
from .registry import Registry, RegistryRow
from .schema import Strategy
from .transitions import PAPER, RESEARCH

FILE_PATTERN = "*.yaml"


@dataclass(frozen=True)
class Drift:
    strategy: Strategy
    reason: str


@dataclass(frozen=True)
class Playbook:
    strategies: tuple[Strategy, ...]
    registered: frozenset[tuple[str, int]] = frozenset()  # versions with a registry row (their rule is frozen)
    drifted: tuple[Drift, ...] = ()  # paper versions whose live feature drifted: not approved, to be paused

    def shadow(self) -> tuple[Strategy, ...]:
        """Registered research candidates: forward-tested in shadow (owner, 14 Oct 2026), never in a book's account.
        An unregistered candidate is not frozen, so it is not tested."""
        return tuple(s for s in self.strategies if s.status == RESEARCH and s.key in self.registered)

    def approved(self) -> tuple[Strategy, ...]:
        """The versions Book 1 may trade today (status `paper`, live features still valid); empty when none."""
        drifted = {d.strategy.key for d in self.drifted}
        return tuple(s for s in self.strategies if s.status == PAPER and s.key not in drifted)

    def get(self, name: str, version: int) -> Strategy:
        found = [s for s in self.strategies if s.key == (name, version)]
        if not found:
            raise PlaybookError(f"{name} v{version}", "no such playbook file")
        return found[0]


class PlaybookLoader:
    def __init__(self, folder: Path, registry: Registry, checks: Sequence[ApprovalCheck]):
        self.folder, self.registry, self.checks = folder, registry, tuple(checks)

    def load(self) -> Playbook:
        strategies = self._read_files()
        rows, drifted = self.registry.rows(), []
        for strategy in strategies:
            history = [row for row in rows if row.key == strategy.key]
            try:
                self.check_against_history(strategy, history)
            except LiveFeatureDrift as drift:
                if strategy.status != PAPER:
                    raise
                drifted.append(Drift(strategy, str(drift)))
        self._require_files_for(rows, {s.key for s in strategies})
        return Playbook(tuple(strategies), frozenset(row.key for row in rows), tuple(drifted))

    def check_against_history(self, strategy: Strategy, history: Sequence[RegistryRow]) -> None:
        """The file matches its registered fingerprint and latest status, and passes the checks for that status."""
        where = strategy.file_name
        latest = history[-1] if history else None
        if latest and latest.sha256 != strategy.parameters_sha256:
            raise PlaybookError(
                f"{where}: rule", "differs from the registered version: a changed rule is a new version"
            )
        registered = latest.status if latest else RESEARCH
        if strategy.status != registered:
            raise PlaybookError(f"{where}: status", f"is {strategy.status} but the registry says {registered}")
        approval = next((row for row in reversed(history) if row.status == PAPER), None)
        try:
            run_checks(self.checks, strategy, approval)
        except PlaybookError as refused:
            raise type(refused)(f"{where}: {refused.field}", refused.reason) from None

    def _read_files(self) -> list[Strategy]:
        paths = sorted(self.folder.glob(FILE_PATTERN)) if self.folder.is_dir() else []
        strategies = [strategy_from_text(path.read_text(encoding="utf-8"), path.name) for path in paths]
        seen: dict[tuple[str, int], str] = {}
        for path, strategy in zip(paths, strategies, strict=True):
            if strategy.key in seen:
                raise PlaybookError(f"{seen[strategy.key]} and {path.name}", "same name and version in two files")
            seen[strategy.key] = path.name
        for path, strategy in zip(paths, strategies, strict=True):
            if path.name != strategy.file_name:
                raise PlaybookError(path.name, f"must be named {strategy.file_name} (its name and version)")
        return strategies

    @staticmethod
    def _require_files_for(rows: Sequence[RegistryRow], present: set[tuple[str, int]]) -> None:
        for row in rows:
            if row.key not in present:
                raise PlaybookError(f"{row.name} v{row.version}", "registered but its playbook file is missing")


def registry_path(folder: Path) -> Path:
    return folder / PLAYBOOK_REGISTRY_FILE
