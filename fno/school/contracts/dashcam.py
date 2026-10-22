"""The dashcam port (story 3.4): write-once files of records, the decisions file sealed before any fill."""

from datetime import date
from typing import Protocol, runtime_checkable

from ..constants import RecordKind
from .seal import Seal
from .slot_file import SlotRecord


class ReplayConflict(Exception):
    """Other bytes for a (session, slot, kind) already sealed: never overwritten, reported as "rule broken"."""


@runtime_checkable
class DashcamStore(Protocol):
    def seal(self, session: date, slot: str, kind: RecordKind, records: tuple[SlotRecord, ...]) -> Seal:
        """Encode with `encode_slot_file`, save once and push its receipt; the same records again return the same seal,
        other records for the same key raise `ReplayConflict`."""

    def read(self, seal: Seal) -> tuple[SlotRecord, ...]:
        """The sealed records, their bytes checked against the seal's SHA-256 (`StaleSeal` if they differ)."""
