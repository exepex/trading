"""Where recommendations go (story REC1b, section 5): Drive, written once through O9's `DataStore`, with the receipt
committed and pushed to `main` before anything is posted (the school dashcam's pattern). The same day again with the
same bytes changes nothing; other bytes are refused, never written over."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date

from ..storage.raw_store import RawFileConflict
from ..storage.receipt_publisher import ReceiptPublisher
from .codec import encode
from .contracts import Recommendation

AREA_FOLDER = "recommend"
RECEIPT_MESSAGE = "Receipt: the recommendation of {day}"
CONFLICT = "{path}: a different recommendation is already recorded for {day}; nothing was written over it"


class NotSaved(Exception):
    """The record or its receipt could not be saved and pushed: nothing may be posted."""


@dataclass(frozen=True)
class Saved:
    path: str  # the record's Drive path inside the data area
    sha256: str
    receipt_commit: str


def record_path(day: date) -> str:
    return f"{AREA_FOLDER}/{day:%Y}/{day:%m}/{day.isoformat()}.json"


class DriveRecommendations:
    def __init__(self, data, publisher: ReceiptPublisher):
        """`data`: O9's `DataStore` for the data area; `publisher`: commits and pushes the receipt to `main`."""
        self.data, self.publisher = data, publisher

    def save(self, record: Recommendation) -> Saved:
        path, payload = record_path(record.session), encode(record)
        digest = hashlib.sha256(payload).hexdigest()
        drive_path = f"{self.data.area}/{path}"
        existing = self.publisher.published(drive_path)  # judged on the remote's receipt, before Drive is touched
        if existing is not None:
            if existing.sha256 != digest:
                raise NotSaved(CONFLICT.format(path=path, day=record.session))
            return Saved(path, digest, existing.commit)
        try:
            receipt = self.data.put(path, payload)
            pushed = self.publisher.publish(receipt.path, RECEIPT_MESSAGE.format(day=record.session))
        except RawFileConflict:
            raise NotSaved(CONFLICT.format(path=path, day=record.session)) from None
        except Exception as failed:  # a refused push, a Drive error: never posted, named by type only (no secret)
            raise NotSaved(f"{path}: {type(failed).__name__}") from None
        return Saved(path, digest, pushed.commit)
