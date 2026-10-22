"""The dashcam port (story 3.4): write-once records sealed before any fill."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol, runtime_checkable


class ReplayConflict(Exception):
    """Other bytes for a key already sealed: never overwritten, reported as "rule broken"."""


class StaleSeal(Exception):
    """A seal not pushed, pushed after the fill time, or naming another file's SHA-256."""


@dataclass(frozen=True)
class Seal:
    path: str  # the record file's Drive path
    sha256: str
    pushed_at: datetime  # when its receipt reached the remote
    commit: str  # the receipt's commit

    def __post_init__(self):
        if self.pushed_at.tzinfo is None or not self.sha256 or not self.commit:
            raise ValueError("a seal needs an aware push time, a SHA-256 and a commit")

    def covers(self, sha256: str, fill_time: datetime) -> bool:
        """True when this seal is for that file and was pushed no later than the fill."""
        return self.sha256 == sha256 and self.pushed_at <= fill_time


@runtime_checkable
class DashcamStore(Protocol):
    def seal(self, session: date, slot: str, payload: bytes) -> Seal:
        """Save once and push its receipt; the same bytes again return the same seal, other bytes raise
        `ReplayConflict`."""

    def read(self, seal: Seal) -> bytes:
        """The sealed bytes, checked against the seal's SHA-256."""
