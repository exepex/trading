"""The counting rule (story MS-P1h, D6's rule): a decision counts only if the comparison card and the driver's version
row were frozen in commits strictly before the decision's own commit, the driver's card is the one its row names, and
the session is on or after the first counted session. Anything else is kept in the denominator, never dropped."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Protocol

from ..constants import RoadCode

CARD_PATH = "research/school/CARD_P1.md"


class NotCounted(StrEnum):
    NO_FIRST_COUNTED_SESSION = "no_first_counted_session"
    BEFORE_FIRST_COUNTED_SESSION = "before_first_counted_session"
    CARD_NOT_FROZEN_BEFORE = "card_not_frozen_before"
    VERSION_NOT_REGISTERED_BEFORE = "version_not_registered_before"
    DRIVER_CARD_CHANGED = "driver_card_changed"


@dataclass(frozen=True)
class CountCandidate:
    """What a sealed decision gives the rule: its place, the driver card it ran on and the commit that holds it."""

    session: date
    road: RoadCode
    driver_id: str  # e.g. "CS1@1"
    card_sha256: str
    commit: str


@dataclass(frozen=True)
class CountVerdict:
    counted: bool
    reason: NotCounted | None = None


class CardHistory(Protocol):
    def last_commit(self, path: str) -> str | None:
        """The newest commit that changed the file, or None when it was never committed."""

    def is_ancestor(self, older: str, newer: str) -> bool: ...


class VersionLookup(Protocol):
    def card_sha256_registered_before(self, driver_id: str, session: date, decision_commit: str) -> str | None:
        """The card SHA-256 of the driver's active version whose row and components were committed strictly before the
        decision's commit (D6's ancestry rule), or None when there is none."""


class CountingRule:
    def __init__(self, first_counted: date | None, history: CardHistory, versions: VersionLookup):
        self.first_counted, self.history, self.versions = first_counted, history, versions

    def verdict(self, candidate: CountCandidate) -> CountVerdict:
        if self.first_counted is None:
            return CountVerdict(False, NotCounted.NO_FIRST_COUNTED_SESSION)
        if candidate.session < self.first_counted:
            return CountVerdict(False, NotCounted.BEFORE_FIRST_COUNTED_SESSION)
        if not self._frozen_before(CARD_PATH, candidate.commit):
            return CountVerdict(False, NotCounted.CARD_NOT_FROZEN_BEFORE)
        registered = self.versions.card_sha256_registered_before(
            candidate.driver_id, candidate.session, candidate.commit
        )
        if registered is None:
            return CountVerdict(False, NotCounted.VERSION_NOT_REGISTERED_BEFORE)
        if registered != candidate.card_sha256:
            return CountVerdict(False, NotCounted.DRIVER_CARD_CHANGED)
        return CountVerdict(True)

    def _frozen_before(self, path: str, decision_commit: str) -> bool:
        """Strictly before: the card's last change is an ancestor of, and not, the decision's own commit."""
        frozen = self.history.last_commit(path)
        return frozen is not None and frozen != decision_commit and self.history.is_ancestor(frozen, decision_commit)
