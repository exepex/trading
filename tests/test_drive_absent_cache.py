"""O9-child (the dry run's `price_ranges` finding, 24 Oct): a Drive store instance never keeps an absence. One instance
looks a path up and finds nothing; another instance of the same process creates it; the first must then find it
(D1). A found ID is still cached (D2). The write-then-read of one step, through `DataStore` and `DriveCache` on two
instances, works on the real root and under `dryrun/` (D3), and `price_ranges`' close tables read back a table their
own step just wrote with a cold or a warm local cache (D4). An absent path stays absent (D5)."""

from datetime import date

import pytest

from fno.price_ranges.folders import CLOSES, closes_path, drive
from fno.price_ranges.tables import CloseTables
from fno.rehearsal.drive import DryrunDrive
from fno.storage.data_store import DataStore
from fno.storage.drive_cache import DriveCache
from fno.storage.google_drive import DRIVE_FILES_URL
from fno.storage.receipts import ReceiptFolder
from tests.dr1.fake_drive import FakeDrive, store_on

OLD, NEW = b"date,close\n2026-10-21,1\n", b"date,close\n2026-10-21,1\n2026-10-22,2\n"
OLD_PATH = closes_path("BANKNIFTY", date(2026, 10, 21), 2414, "c7457fef611a")
NEW_PATH = closes_path("BANKNIFTY", date(2026, 10, 22), 2415, "ea232e876681")


class Counting(FakeDrive):
    """Counts Drive's list calls (each `_child` lookup is one)."""

    def __init__(self):
        super().__init__()
        self.lists = 0

    def get(self, url, params=None, timeout=None):
        self.lists += url == DRIVE_FILES_URL
        return super().get(url, params, timeout)


# D1: two instances, the first must find what the second created


@pytest.mark.parametrize("path", ["x.json", "a/x.json", "a/b/c/x.json"])
def test_an_absence_one_instance_saw_never_hides_what_another_created(path):
    remote = FakeDrive()
    reader, writer = store_on(remote), store_on(remote)
    assert reader.get(path) is None  # every folder of the path absent, then the file
    writer.put(path, b"made")
    assert reader.get(path) == b"made"


def test_the_last_folder_absent_under_a_folder_that_exists():
    remote = FakeDrive()
    reader, writer = store_on(remote), store_on(remote)
    writer.put("a/other.json", b"o")
    assert reader.get("a/b/x.json") is None  # `a` found and cached, `b` absent
    writer.put("a/b/x.json", b"made")
    assert reader.get("a/b/x.json") == b"made"


# D2: found IDs still cached; an absent name asked again


def test_a_found_file_s_folders_are_not_asked_twice_and_an_absent_name_is():
    remote = Counting()
    store_on(remote).put("a/b/x.json", b"made")
    reader = store_on(remote)
    reader.get("a/b/x.json")
    first = remote.lists
    reader.get("a/b/x.json")
    assert remote.lists == first  # a, b and x.json all cached: only the download
    reader.get("a/b/none.json")
    asked = remote.lists
    reader.get("a/b/none.json")
    assert remote.lists == asked + 1  # the absent name asked again; its found folders not


# D5: empty


def test_an_absent_path_stays_absent_and_nothing_is_created():
    remote = FakeDrive()
    reader = store_on(remote)
    assert reader.get("a/b/x.json") is None and reader.get("a/b/x.json") is None
    assert remote.items == {}


# D3 and D4: one step's write, then its read, on two instances


def step(remote, tmp_path, rehearsal: bool):
    """A step's two store instances, as `build_data_store` and `build_drive_cache` make them."""
    writer, reader = store_on(remote), store_on(remote)
    if rehearsal:
        writer, reader = (DryrunDrive(s, "dryrun/r1", lambda path: path == drive(OLD_PATH)) for s in (writer, reader))
    receipts = ReceiptFolder(tmp_path / "receipts")
    return DataStore(writer, "data", receipts, "pricerange", "r1"), DriveCache(reader, receipts, tmp_path / "cache")


def old_table(remote, tmp_path):
    """The table the record held before the step: in the real root, with its receipt."""
    store_on(remote).put(drive(OLD_PATH), OLD)
    DataStore(store_on(remote), "data", ReceiptFolder(tmp_path / "receipts"), "pricerange", "r0").put(OLD_PATH, OLD)


@pytest.mark.parametrize("rehearsal", [False, True], ids=["real", "rehearsal"])
def test_a_step_reads_back_what_it_just_wrote_with_a_cold_cache(tmp_path, rehearsal):
    remote = FakeDrive()
    old_table(remote, tmp_path)
    data, cache = step(remote, tmp_path, rehearsal)
    assert cache.sync(drive(CLOSES)).complete  # cold: reads the old table (and looks under `dryrun/`)
    data.put(NEW_PATH, NEW)
    report = cache.sync(drive(CLOSES))
    assert report.complete, report.problems
    assert cache.local(drive(NEW_PATH)).read_bytes() == NEW


@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
def test_price_ranges_close_tables_read_their_own_new_table_back(tmp_path, warm):
    """The dry run's failing read: `latest_text` before and after the step's own write, under `dryrun/`."""
    remote = FakeDrive()
    old_table(remote, tmp_path)
    data, cache = step(remote, tmp_path, rehearsal=True)
    if warm:  # the earlier, passing run: the old table already on disk
        target = cache.local(drive(OLD_PATH))
        target.parent.mkdir(parents=True)
        target.write_bytes(OLD)
    tables = CloseTables(data, ReceiptFolder(tmp_path / "receipts"), cache)
    assert tables.latest_text("BANKNIFTY") == OLD.decode()
    data.put(NEW_PATH, NEW)  # as `CloseTables.update` writes it
    assert tables.latest_text("BANKNIFTY") == NEW.decode()
