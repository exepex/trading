"""Story A16 criteria 1, 3 and 5 with two writers on one Drive (judge 108 addendum 3, should-fix 1; orchestrator
decision 39): copies are content-addressed, so two runs taking one mark never write one name, even when their Drive
look-up and create calls interleave; the ledger row names the copy a mark uses, and a mark with copies but no row gets
the smallest name. Also the write-once rule of the row files (mutation I22)."""

from datetime import date, time

import pytest

from fno.intraday.ledger import FIELDS
from fno.intraday.row_files import RowFileExists, write_row
from fno.storage.raw_store import RawFileConflict, RawFileStore, path_parts
from tests.intraday.fakes import DAY, FakeClock, build, ist


class InterleavingDrive(RawFileStore):
    """Drive's own behaviour (`GoogleDriveUploadStore`): `put` looks the name up, then creates a new file, so two
    writers whose look-ups both find nothing create two files of one name; `get` then refuses that name for good.
    `between` runs between a put's look-up and its create: the other writer's whole put happens there."""

    name = "interleaving drive"

    def __init__(self):
        self.files: list[tuple[str, bytes]] = []
        self.between = None

    def get(self, path: str) -> bytes | None:
        found = [data for name, data in self.files if name == path]
        if len(found) > 1:
            raise RawFileConflict(f"{len(found)} items named {path!r} in one Drive folder")
        return found[0] if found else None

    def put(self, path: str, data: bytes) -> None:
        existing = self.get(path)  # the look-up
        if existing is not None:
            if existing != data:
                raise RawFileConflict(path)
            return
        if self.between is not None:
            hook, self.between = self.between, None
            hook()  # the other writer looks up and creates now
        self.files.append((path, data))  # the create

    def checksums(self, folder: str) -> dict[str, str]:
        prefix = f"{folder}/"
        return {name[len(prefix):]: "" for name, _ in self.files if name.startswith(prefix) and "/" not in
                name[len(prefix):]}  # fmt: skip


def test_two_runs_whose_drive_calls_interleave_at_one_mark_never_break_its_reads(tmp_path):
    drive = InterleavingDrive()
    first, *_ = build(tmp_path / "a", FakeClock(ist(DAY, 9, 14)), drive=drive)
    second, second_source, *_ = build(tmp_path / "b", FakeClock(ist(DAY, 9, 14, 30)), drive=drive)
    second_source.latency = 2.0  # two real runs never get byte-identical answers
    drive.between = lambda: second.snapshot()  # the second run's look-up and create land inside the first's put
    outcome = first.snapshot()
    assert outcome.status == "good"
    names = [path_parts(name)[-1] for name, _ in drive.files]
    assert len(names) == 2 and len(set(names)) == 2 and all(n.startswith("nifty_20261015_0915_") for n in names)
    for recorder in (first, second):  # each run's row names its own copy, and reading it works
        [row] = recorder.ledger.rows(DAY)
        assert drive.get(f"raw/{row['raw_path']}") is not None and row["status"] == "good"
    first.run(time(9, 35))  # the next mark's settle reads 09:15's copy through the row: no conflict
    assert [r["status"] for r in first.ledger.rows(DAY)] == ["good", "good"]


def test_a_due_mark_with_copies_but_no_row_uses_the_smallest_name(tmp_path):
    clock = FakeClock(ist(DAY, 9, 14))
    recorder, source, _, _, files = build(tmp_path, clock)
    for latency in (1.0, 2.0, 3.0):  # three runs stored a copy and died before writing a row
        clock.moment = ist(DAY, 9, 15)
        source.latency = latency
        files.save(DAY, ist(DAY, 9, 15), source.take(DAY, ist(DAY, 9, 15)).to_bytes())
    smallest = min(files.store.checksums("fakegroww/derivatives/intraday-snapshots/2026/10/15"))
    clock.moment = ist(DAY, 9, 29)
    recorder.snapshot()
    row = recorder.ledger.rows(DAY)[0]
    assert row["raw_path"].endswith(smallest) and row["status"] == "good"


class NoListing(RawFileStore):
    """A store that cannot list a folder (the base class refuses)."""

    def get(self, path: str) -> bytes | None:
        return None

    def put(self, path: str, data: bytes) -> None:
        return None


def test_a_store_that_cannot_list_leaves_an_unrowed_mark_missed(tmp_path):
    clock = FakeClock(ist(DAY, 9, 29))
    recorder, _, _, _, files = build(tmp_path, clock)
    files.store = NoListing()
    recorder.snapshot()
    assert recorder.ledger.rows(DAY)[0]["status"] == "missed"


def test_a_row_file_is_written_once_and_never_rewritten(tmp_path):
    """Judge 108 addendum 3, mutation I22: the write-once check of the row files themselves."""
    path = tmp_path / "slots" / "nifty_20261015_0915.csv"
    write_row(path, FIELDS, dict.fromkeys(FIELDS, "first"))
    before = path.read_text()
    with pytest.raises(RowFileExists):
        write_row(path, FIELDS, dict.fromkeys(FIELDS, "second"))
    assert path.read_text() == before


def test_the_ledger_refuses_a_second_row_for_a_mark(tmp_path):
    clock = FakeClock(ist(DAY, 9, 14))
    recorder, *_ = build(tmp_path, clock)
    recorder.snapshot()
    [row] = recorder.ledger.rows(DAY)
    with pytest.raises(RowFileExists):
        recorder.ledger.append(DAY, [{**row, "status": "stale"}])
    assert recorder.ledger.rows(DAY) == [row]


def test_the_realised_variance_reads_each_marks_copy_through_its_ledger_row(tmp_path):
    clock = FakeClock(ist(date(2026, 10, 14), 9, 10))
    recorder, *_ = build(tmp_path, clock)
    recorder.run(time(15, 35))
    clock.moment = ist(DAY, 9, 10)
    recorder.files.unrowed_copy = lambda day, mark: pytest.fail("a reader resolved a mark without its row")
    recorder.run(time(15, 35))
    assert {r["session"]: r["status"] for r in recorder.session_rv.table.rows()}["2026-10-15"] == "ok"


def test_several_bad_marks_settled_at_once_make_one_send_attempt(tmp_path):
    clock = FakeClock(ist(DAY, 9, 14))
    recorder, _, alerts, *_ = build(tmp_path, clock)
    alerts.failing = True
    recorder.snapshot()
    clock.moment = ist(DAY, 10, 44)  # 09:30, 09:45, 10:00, 10:15 and 10:30 are settled as missed in one go
    recorder.snapshot()
    assert len(alerts.sent) == 1
