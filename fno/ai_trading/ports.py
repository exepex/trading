"""What the AI books' trading runner depends on (story F1t), each behind an interface: the book's decider (F5 for
Book 2, F6 for Book 3), F2's analyst cards, and the routine trigger (O6's `RoutineTrigger`, used unchanged). The
hand-over shape was agreed with F5, F6 and F2 on 16 Oct 2026 (`docs/stories/F1t-ai-trading-runner.md`, "Hand-over
port"). Each book's `OrderBuilder` and `ExitRules` (E3's ports) are also the decider's story's, wired per book in
`fno/daily/wiring.py`."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from ..desk.common_pack import CommonPack
from ..desk.private_pack import PrivatePack


@dataclass(frozen=True)
class DayPacks:
    """The day's packs as E2's pack step wrote them (the private one from its Drive mirror); `OSError` or
    `ValueError` when one is missing or not as written."""

    common: Callable[[date], CommonPack]
    private: Callable[[str, date], PrivatePack]


class DecisionRefused(Exception):
    """The decider cannot write a run for this answer (for example its private pack does not rebuild); the message
    says why. The book-day is `refused`: no trade."""


@dataclass(frozen=True)
class AcceptedDecision:
    """An on-time, revealed, valid answer from the registered model, with everything the decider may use."""

    book: str
    day: date
    version: str  # the decision version's label (it names the role units, the model and the isolation)
    registered_model: str
    model_reported: str  # equal to `registered_model`: anything else never reaches a decider
    session: str  # the fire log's session link: D3's `session_id`
    common_pack: CommonPack
    private_pack: PrivatePack
    decision: dict  # the book's own object, already through its shape check
    analyst_cards: dict  # F2's item exactly as fired (card IDs, role_set_version, input_sha256)
    consulted_units: tuple[str, ...]  # the units whose card was in that item: what was given (F9b withholds it)
    commitment_commit: str
    reveal_commit: str


@dataclass(frozen=True)
class DecidedRun:
    run: Path  # journal/<book>/decisions/<d>/<run_id>/, written by the decider (DecisionStore, atomic)
    files: tuple[Path, ...] = field(default=())  # other files to commit with it (C4's log, registry rows, shadows)


class AiBookDecider(ABC):
    @abstractmethod
    def decide(self, accepted: AcceptedDecision) -> DecidedRun:
        """Writes one D3 run with C2 and C4 inside (a blocked action still gets a "no trade, blocked" run with the
        attempt recorded); `DecisionRefused` when no run can be written."""


class AnalystCards(ABC):
    """F2's cards of the day as one pointer item; never raises (a missing file makes every role `no_submission`)."""

    @abstractmethod
    def item(self, day: date, role_units: Sequence[str]) -> dict:
        """F2's item `{"day", "input_sha256", "role_set_version", "roles": [{"role", "unit_id", "status", "reason",
        "card_id", "card"}]}`: every registered role's entry, `card` null unless the status is usable."""


class NoAnalystCards(AnalystCards):
    """Until F2's cards exist: an item with no roles, so a version consulting no units is fired as usual."""

    def item(self, day: date, role_units: Sequence[str]) -> dict:
        return {"day": day.isoformat(), "input_sha256": "", "role_set_version": "", "roles": []}


USABLE_CARD_STATUSES = ("valid", "not_applicable")  # F2's statuses whose card is passed to the book


def consulted_units(item: dict) -> tuple[str, ...]:
    """The units whose card was in the item (F2's definition, agreed 16 Oct)."""
    return tuple(sorted(r["unit_id"] for r in item.get("roles", []) if r.get("status") in USABLE_CARD_STATUSES))
