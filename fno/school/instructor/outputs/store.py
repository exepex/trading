"""The instructor's own write-once files (story MS-INS, part e): one gzip of canonical JSON lines per (session, kind)
under `school/instructor/` in O9's data area, its receipt committed and pushed through the dashcam's publisher. Equal
records give equal bytes, so a rerun is a no-op; other bytes for a written key are refused. It never writes into the
dashcam: its paths are its own folder's. A run that stopped after a Drive write and before its receipt reached main is
recovered from the stored bytes, never recomputed (MS-P1j's builder, 23 Oct 2026)."""

import hashlib
from datetime import date

from ....storage.data_store import DataStore
from ....storage.raw_store import RawFileConflict
from ....storage.receipts import Receipt
from ...contracts.seal import StaleSeal
from ...dashcam.names import SCHOOL_AREA
from ...dashcam.publisher import ReceiptPublisher
from ...dashcam.reader import SlotFileReader
from ..ports import InstructorConflict, InstructorKind, InstructorRecord
from ..records_file import decode_instructor_file, encode_instructor_file

INSTRUCTOR_FOLDER = f"{SCHOOL_AREA}/instructor"
OTHER_BYTES = "{path} is written with other bytes; an instructor file is never overwritten"
RECEIPT_MESSAGE = "instructor {kind} {session}"
DAMAGED = "{path} holds other bytes than its receipt's SHA-256"


def instructor_path(session: date, kind: InstructorKind) -> str:
    """Relative to the data store's area, e.g. `school/instructor/2026/11/02.causes.jsonl.gz`."""
    return f"{INSTRUCTOR_FOLDER}/{session:%Y/%m/%d}.{kind}.jsonl.gz"


class DriveInstructorStore:
    def __init__(self, data: DataStore, publisher: ReceiptPublisher, reader: SlotFileReader):
        self.data, self.publisher, self.reader = data, publisher, reader

    def write(self, session: date, kind: InstructorKind, records: tuple[InstructorRecord, ...]) -> str:
        path, payload = instructor_path(session, kind), encode_instructor_file(records)
        sha256 = hashlib.sha256(payload).hexdigest()
        existing = self.publisher.published(f"{self.data.area}/{path}")
        if existing is not None:
            if existing.sha256 != sha256:
                raise InstructorConflict(OTHER_BYTES.format(path=path))
            return sha256
        try:
            receipt = self.data.put(path, payload)
        except RawFileConflict as conflict:
            raise InstructorConflict(OTHER_BYTES.format(path=path)) from conflict
        self._publish(session, kind, receipt)
        return receipt.sha256

    def _publish(self, session: date, kind: InstructorKind, receipt: Receipt) -> None:
        self.publisher.publish(receipt.path, RECEIPT_MESSAGE.format(kind=kind, session=session))

    def recover(self, session: date, kind: InstructorKind) -> tuple[InstructorRecord, ...] | None:
        """The records written for that key, publishing the receipt first when Drive holds the file and main has no
        receipt for it: a later run sees more and could compute other records, which write-once would refuse for
        good. Drive's bytes are the record (the same bytes put again are a no-op there)."""
        path = instructor_path(session, kind)
        if self.publisher.published(f"{self.data.area}/{path}") is None:
            stored = self.data.drive.get(f"{self.data.area}/{path}")
            if stored is None:
                return None
            self._publish(session, kind, self.data.put(path, stored))
        return self.read(session, kind)

    def read(self, session: date, kind: InstructorKind) -> tuple[InstructorRecord, ...] | None:
        path = instructor_path(session, kind)
        pushed = self.publisher.published(f"{self.data.area}/{path}")
        if pushed is None:
            return None
        data = self.reader.read(path)
        if hashlib.sha256(data).hexdigest() != pushed.sha256:
            raise StaleSeal(DAMAGED.format(path=path))
        return decode_instructor_file(data)
