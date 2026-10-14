"""What the daily run depends on (story E3), each behind an interface so a fake can stand in for it in tests and a
real part can be swapped in the composition root: the common pack, the books' committed decisions, the execution
capture, C4's validity gate, the exit rules, the account writes across containers and the commits."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import TypeVar

from ..checks.data_checks import CaptureRecord
from .common_pack import CommonPack
from .entries import EntryOrder
from .exit_rules import ExitRule
from .records import DeskJournal

T = TypeVar("T")


@dataclass(frozen=True)
class CommittedDecision:
    """A book's decision run as committed: its run ID, when its commit happened, and the entry orders it decided."""

    book: str
    run_id: str
    committed_at: datetime  # time zone aware
    orders: tuple[EntryOrder, ...]  # empty for a "no trade" decision


class Waiter(ABC):
    @abstractmethod
    def until(self, moment: datetime) -> None:
        """Returns at `moment` (at once when it has passed)."""


class Committer(ABC):
    @abstractmethod
    def commit(self, paths: Sequence[Path], message: str) -> str:
        """Pulls, commits these paths and pushes; the commit ID. Raises when it cannot."""


class Packs(ABC):
    @abstractmethod
    def build(self, day: date) -> CommonPack:
        """Builds and writes the day's common pack (E2); `PackError` while the canonical snapshot is not committed."""

    @abstractmethod
    def stored(self, day: date) -> CommonPack | None:
        """The day's written common pack; None when none was written."""

    @abstractmethod
    def files(self, day: date) -> tuple[Path, ...]:
        """The day's written pack files, to commit."""


class VersionKeeper(ABC):
    @abstractmethod
    def keep(self, day: date) -> str:
        """Registers (and commits) a new D6 version of Book 1 when its served playbook changed; one line saying what."""


class DecisionSource(ABC):
    @abstractmethod
    def committed(self, book: str, day: date, deadline: datetime) -> CommittedDecision | None:
        """The book's latest decision run committed before `deadline`; None when there is none."""


class OrderBuilder(ABC):
    """A committed decision run's entry orders (E5 for Book 1; F5 and F6 for the AI books)."""

    @abstractmethod
    def orders(self, book: str, run: Path) -> Sequence[EntryOrder]:
        """The orders the run decided (empty for "no trade")."""


class ExecutionCapture(ABC):
    @abstractmethod
    def capture(self, day: date) -> CaptureRecord | None:
        """Takes one execution capture now (a second recorder capture, A4's rules), writes and commits its capture
        record; None when no capture could be taken."""


class ValidityGate(ABC):
    """C4's hard-validity checks on a committed decision (story C4, built apart)."""

    @abstractmethod
    def problems(self, decision: CommittedDecision, order: EntryOrder) -> list[str]:
        """Why this order may not be filled; empty only after a completed C4 pass."""


class ExitRules(ABC):
    @abstractmethod
    def rules(self, book: str) -> Mapping[str, Sequence[ExitRule]]:
        """Each open trade's exit rules, from its playbook version (by trade ID)."""


class AccountSync(ABC):
    @abstractmethod
    def write(self, book: str, apply: Callable[[DeskJournal], T], message: str) -> T:
        """Runs `apply` on the book's journal under its lock and makes the write durable across containers."""
