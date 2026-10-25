"""Where recommendations go (story REC1b, section 5): Drive, written once through O9's `DataStore`, with the receipt
committed and pushed to `main` before anything is posted (the school dashcam's pattern). A day already receipted is
never written or posted again. A record on Drive with no receipt (a save stopped before its push) is adopted, as the
dashcam's `recover` does: its bytes must read strictly as that day's recommendation, its receipt is then pushed, and
the first-made record stands; a later run never writes other bytes over it."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date

from ..storage.raw_store import RawFileConflict
from ..storage.receipt_publisher import ReceiptPublisher
from .codec import decode, encode
from .contracts import Recommendation, RecordRefused

AREA_FOLDER = "recommend"
RECEIPT_MESSAGE = "Receipt: the recommendation of {day}"
CONFLICT = "{path}: Drive holds other bytes for {day}; nothing was written over them"
STUCK = "{path}: Drive holds bytes for {day} that are not its recommendation ({why}); nothing was written over them"
PROGRAMMING_ERRORS = (TypeError, KeyError, AttributeError, NameError)  # a bug keeps its traceback


class NotSaved(Exception):
    """The record or its receipt could not be saved and pushed: nothing may be posted."""


@dataclass(frozen=True)
class Saved:
    path: str  # the record's Drive path inside the data area
    sha256: str
    receipt_commit: str


@dataclass(frozen=True)
class Stored:
    record: Recommendation  # the day's record as it stands: an adopted earlier one wins over a new one
    saved: Saved
    already: bool  # receipted before this run: not posted again
    adopted: bool  # found on Drive without a receipt and receipted now


def record_path(day: date) -> str:
    return f"{AREA_FOLDER}/{day:%Y}/{day:%m}/{day.isoformat()}.json"


class DriveRecommendations:
    def __init__(self, data, publisher: ReceiptPublisher):
        """`data`: O9's `DataStore` for the data area; `publisher`: commits and pushes the receipt to `main`."""
        self.data, self.publisher = data, publisher

    def save(self, record: Recommendation) -> Stored:
        path = record_path(record.session)
        try:
            return self._save(record, path, f"{self.data.area}/{path}")
        except (NotSaved, *PROGRAMMING_ERRORS):
            raise
        except RawFileConflict:
            raise NotSaved(CONFLICT.format(path=path, day=record.session)) from None
        except Exception as failed:  # a refused push, a Drive error: never posted, named by type only (no secret)
            raise NotSaved(f"{path}: {type(failed).__name__}") from None

    def _save(self, record: Recommendation, path: str, drive_path: str) -> Stored:
        existing = self.publisher.published(drive_path)  # judged on the remote's receipt, before Drive is touched
        held = self.data.drive.get(drive_path)
        if existing is not None:
            return Stored(self._day_record(held, record.session, path), Saved(path, existing.sha256, existing.commit),
                          already=True, adopted=False)  # fmt: skip
        chosen = record if held is None else self._day_record(held, record.session, path)
        payload = encode(chosen)
        receipt = self.data.put(path, payload)  # the same bytes as Drive holds: a no-op, the receipt written
        pushed = self.publisher.publish(receipt.path, RECEIPT_MESSAGE.format(day=record.session))
        return Stored(chosen, Saved(path, hashlib.sha256(payload).hexdigest(), pushed.commit),
                      already=False, adopted=held is not None)  # fmt: skip

    @staticmethod
    def _day_record(held: bytes | None, day: date, path: str) -> Recommendation:
        if held is None:
            raise NotSaved(STUCK.format(path=path, day=day, why="receipted but missing on Drive"))
        try:
            stored = decode(held)
        except RecordRefused as refused:
            raise NotSaved(STUCK.format(path=path, day=day, why=refused)) from None
        if stored.session != day:
            raise NotSaved(STUCK.format(path=path, day=day, why=f"a record of {stored.session}"))
        return stored
