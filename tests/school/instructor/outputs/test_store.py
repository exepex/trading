"""Part e's store (story MS-INS, criteria 1-2): the instructor's own files, write-once under `school/instructor/`, a
receipt published for each; the same bytes again a no-op, other bytes refused, damaged bytes never read."""

import hashlib
from datetime import UTC, date, datetime

import pytest

from fno.school.contracts.seal import StaleSeal
from fno.school.dashcam.publisher import PushedReceipt
from fno.school.instructor.outputs.store import DriveInstructorStore, instructor_path
from fno.school.instructor.ports import InstructorConflict, InstructorKind
from fno.storage.raw_store import RawFileConflict
from fno.storage.receipts import Receipt
from tests.school.instructor.builders import attribution
from tests.school.instructor.conformance import check_instructor_store

DAY = date(2026, 11, 4)


class FakeData:
    area = "data"

    def __init__(self):
        self.files, self.drive = {}, self  # `drive`: the whole project folder, as DataStore's

    def get(self, drive_path):
        return self.files.get(drive_path.removeprefix(f"{self.area}/"))

    def put(self, path, payload):
        if self.files.get(path, payload) != payload:
            raise RawFileConflict(path)
        self.files[path] = payload
        sha = hashlib.sha256(payload).hexdigest()
        return Receipt(f"{self.area}/{path}", sha, len(payload), "2026-11-04T10:00:00+00:00", "test", "run")


class FakePublisher:
    def __init__(self):
        self.pushed = {}

    def publish(self, drive_path, what):
        sha = self.data.files[drive_path.split("/", 1)[1]]
        self.pushed[drive_path] = PushedReceipt("c0ffee", datetime(2026, 11, 4, tzinfo=UTC),
                                                hashlib.sha256(sha).hexdigest())  # fmt: skip
        return self.pushed[drive_path]

    def published(self, drive_path):
        return self.pushed.get(drive_path)


class FakeReader:
    def __init__(self, data):
        self.data, self.damage = data, False

    def read(self, path):
        return b"damaged" if self.damage else self.data.files[path]


def store():
    data, publisher = FakeData(), FakePublisher()
    publisher.data = data
    return DriveInstructorStore(data, publisher, FakeReader(data))


def test_the_drive_store_conforms():
    check_instructor_store(store(), DAY, (attribution(),), (attribution(theta=76.0, residual=-1.0),))


def test_its_files_live_in_the_instructors_own_folder_never_the_dashcams():
    assert instructor_path(DAY, InstructorKind.CAUSES) == "school/instructor/2026/11/04.causes.jsonl.gz"


def test_a_file_whose_bytes_differ_from_its_receipt_is_never_read():
    kept = store()
    kept.write(DAY, InstructorKind.ATTRIBUTION, (attribution(),))
    kept.reader.damage = True
    with pytest.raises(StaleSeal):
        kept.read(DAY, InstructorKind.ATTRIBUTION)


def test_a_write_the_drive_refuses_is_a_conflict():
    kept = store()
    kept.data.files["school/instructor/2026/11/04.causes.jsonl.gz"] = b"other"
    with pytest.raises(InstructorConflict):
        kept.write(DAY, InstructorKind.CAUSES, (attribution(),))
