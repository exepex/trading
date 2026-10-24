"""For `data`-marked tests (story O9b): the moved data read from the local verified cache only, never from Drive (the
test guards block the network). Run `python -m fno data-cache sync <prefix>` first; a file missing from the cache
fails the test with that command."""

from __future__ import annotations

from fno.storage.data_store import DataStore
from fno.storage.data_wiring import DATA_AREA, DRIVE_CACHE_FOLDER, receipt_folder
from fno.storage.drive_cache import DriveCache
from fno.storage.raw_store import RawFileStore
from fno.storage.wiring import REPOSITORY

NOT_SYNCED = "{path} is not in the verified cache: run `python -m fno data-cache sync {prefix}` first"


class CacheOnlyDrive(RawFileStore):
    """Stands in for Drive in the test process: any call means the cache was not synced."""

    def get(self, path: str) -> bytes | None:
        raise AssertionError(NOT_SYNCED.format(path=path, prefix="/".join(path.split("/")[:2])))

    def put(self, path: str, data: bytes) -> None:
        raise AssertionError(f"a data test tried to write {path}")


def cached_series(kind, folder: str):
    """A receipt-backed series (`ReceiptedRowLog` or `ReceiptedSnapshots`) reading the verified cache only."""
    drive, receipts = CacheOnlyDrive(), receipt_folder()
    store = DataStore(drive, DATA_AREA, receipts, "data-test", "read-only")
    return kind(store, DriveCache(drive, receipts, REPOSITORY / DRIVE_CACHE_FOLDER), folder)
