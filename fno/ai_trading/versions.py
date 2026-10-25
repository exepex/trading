"""The registered decision version of each AI book (story F1t, design D6): its decision prompt and that prompt's
SHA-256, the model the routine must run on, the book's answer shape check, the paths its decider may write, the
analyst role units it consults (F2) and the isolation mode. A prompt changes only as a new version; `brief` refuses a
prompt whose bytes differ from the registered hash. F5 (Book 2) and F6 (Book 3) each add one entry to `VERSIONS`
when their decider lands; until then a live book has no version and is never fired (`not_fired`)."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from ..book3.answer import check_decision as book3_check_decision
from ..constants import BOOK3_AI, ISOLATION_SEALED_SAME_DAY

# `check_decision(decision) -> problems`: empty means ok; standard library only (it runs in the routine's `seal`)
ShapeCheck = Callable[[dict], list[str]]


class VersionRefused(ValueError):
    """The book, version or prompt is not the registered one."""


@dataclass(frozen=True)
class DecisionVersion:
    book: str
    number: int
    prompt_file: str  # repository path of the book's decision prompt (F5's or F6's)
    prompt_sha256: str
    registered_model: str  # a different or unknown served model means no trade (orchestrator ruling, 16 Oct 2026)
    shape_check: ShapeCheck
    write_paths: tuple[str, ...]  # what the decider may write; F1t commits only these and restores them on a refusal
    role_units: tuple[str, ...] = field(default=())  # F2's analyst units the book consults (part of the version)
    role_set_version: str = ""  # F2's role set the units belong to
    isolation: str = ISOLATION_SEALED_SAME_DAY

    @property
    def label(self) -> str:
        return f"{self.book}/decision/v{self.number}/sha256:{self.prompt_sha256}/isolation:{self.isolation}"

    def prompt_text(self, root: Path) -> str:
        data = (Path(root) / self.prompt_file).read_bytes()
        if hashlib.sha256(data).hexdigest() != self.prompt_sha256:
            raise VersionRefused(f"{self.prompt_file} differs from version {self.number}: a change needs a new version")
        return data.decode("utf-8")


class DecisionRegistry:
    def __init__(self, versions: Sequence[DecisionVersion]):
        self.versions = tuple(versions)

    def current(self, book: str) -> DecisionVersion:
        """The book's newest registered decision version."""
        found = [v for v in self.versions if v.book == book]
        if not found:
            raise VersionRefused(f"{book!r} has no registered decision version")
        return max(found, key=lambda v: v.number)

    def by_label(self, label: str) -> DecisionVersion:
        for version in self.versions:
            if version.label == label:
                return version
        raise VersionRefused(f"{label!r} is not a registered decision version")


BOOK3_WRITE_PATHS = ("journal/book3_ai/", "book3/strategies/", "research/ledger.csv")  # never the constitution (D5)
VERSIONS: tuple[DecisionVersion, ...] = (
    DecisionVersion(BOOK3_AI, 1, "agents/book3/decide_v1.md",
                    "93d5fb96ad057a84fe3a3a5b0b027ff3bcb6d2e5010ec3a45b07f8819c2f6de0", "claude-opus-5-5",
                    book3_check_decision, BOOK3_WRITE_PATHS),  # story F6: no role unit until F2's cards exist
)  # fmt: skip  # F5 adds Book 2's entry when its decider lands
REGISTRY = DecisionRegistry(VERSIONS)
