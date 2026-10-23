"""The instructor's own write-once files (story MS-INS, part e): one gzip of canonical JSON lines per (session, kind)
under `school/instructor/` in O9's data area, its receipt committed and pushed through the dashcam's publisher. Equal
records give equal bytes, so a rerun is a no-op; other bytes for a written key are refused. It never writes into the
dashcam: its paths are its own folder's. A run that stopped after a Drive write and before its receipt reached main is
recovered from the stored bytes, never recomputed (MS-P1j's builder, 23 Oct 2026)."""

import hashlib
from datetime import date

from ....storage.data_store import DataStore
from ....storage.raw_store import RawFileConflict
from ...contracts.seal import StaleSeal
from ...dashcam.names import SCHOOL_AREA
from ...dashcam.publisher import ReceiptPublisher
from ...dashcam.reader import SlotFileReader
from ..contracts import Attribution, Classification, PairedRow
from ..ports import InstructorConflict, InstructorKind, InstructorRecord
from ..records_file import decode_instructor_file, encode_instructor_file

INSTRUCTOR_FOLDER = f"{SCHOOL_AREA}/instructor"
OTHER_BYTES = "{path} is written with other bytes; an instructor file is never overwritten"
RECEIPT_MESSAGE = "instructor {kind} {session}"
DAMAGED = "{path} holds other bytes than its receipt's SHA-256"
ADOPTED_MESSAGE = "instructor {kind} {session} adopted: stored on Drive by a run stopped before its receipt"
NOT_ADOPTED = "{path} is on Drive with no receipt and is not this key's instructor file ({why}); not adopted"
KIND_TYPES = {InstructorKind.ATTRIBUTION: Attribution, InstructorKind.CAUSES: Classification,
              InstructorKind.PAIRED: PairedRow}  # fmt: skip


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
        self.publisher.publish(receipt.path, RECEIPT_MESSAGE.format(kind=kind, session=session))
        return receipt.sha256

    def recover(self, session: date, kind: InstructorKind) -> tuple[InstructorRecord, ...] | None:
        """The records written for that key. Drive holding the file with no receipt on main means a run stopped
        between the two: the stored file is adopted (checked to be this key's, its receipt published from its own
        bytes under an "adopted" commit, then read back against that receipt), never recomputed, as a later run sees
        more and write-once would refuse its other records for good. Neither the dashcam nor O9 has such a step."""
        path = instructor_path(session, kind)
        if self.publisher.published(f"{self.data.area}/{path}") is None:
            stored = self.data.drive.get(f"{self.data.area}/{path}")
            if stored is None:
                return None
            _check_stored(path, session, kind, stored)
            receipt = self.data.put(path, stored)  # the same bytes: a no-op on Drive, the receipt written
            self.publisher.publish(receipt.path, ADOPTED_MESSAGE.format(kind=kind, session=session))
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


def _check_stored(path: str, session: date, kind: InstructorKind, stored: bytes) -> None:
    """This key's file: it decodes, re-encodes to the same bytes (canonical), holds only the kind's records, and
    none closed after its session (a re-check writes earlier sessions' records into a later file, never the reverse)."""
    try:
        records = decode_instructor_file(stored)
    except Exception as broken:  # any decoding failure means the bytes are not an instructor file
        raise InstructorConflict(NOT_ADOPTED.format(path=path, why=f"unreadable: {broken}")) from broken
    if encode_instructor_file(records) != stored:
        raise InstructorConflict(NOT_ADOPTED.format(path=path, why="not canonical"))
    if any(not isinstance(r, KIND_TYPES[kind]) for r in records):
        raise InstructorConflict(NOT_ADOPTED.format(path=path, why=f"a record that is not {kind}"))
    if any(getattr(r, "closed_on", session) > session for r in records):
        raise InstructorConflict(NOT_ADOPTED.format(path=path, why=f"a record closed after {session}"))
