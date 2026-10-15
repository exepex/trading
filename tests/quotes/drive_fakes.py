"""A fake private store (Google Drive) for story A4b's tests, with switches for the failure cases."""

from fno.quotes.drive_only_store import DriveOnlyQuoteStore
from fno.quotes.recorder import DATASET
from fno.storage.raw_store import LocalFolderStore, RawFileConflict, RawFileStore
from fno.storage.wiring import OWNER_UPLOAD_SETTINGS

SETTINGS = ", ".join(OWNER_UPLOAD_SETTINGS)


class DriveDown(ConnectionError):
    pass


class FakeDrive(RawFileStore):
    name = "fake drive"

    def __init__(self, down_saves: int = 0):
        self.files: dict[str, bytes] = {}
        self.down_saves = down_saves  # this many saves fail first (Drive down), then saves work

    def get(self, path):
        return self.files.get(path)

    def put(self, path, data):
        if self.down_saves:
            self.down_saves -= 1
            raise DriveDown("drive unreachable (HTTP 503)")
        if path in self.files and self.files[path] != data:
            raise RawFileConflict(path)
        self.files[path] = data


def split_store(folder, drive: RawFileStore | None) -> DriveOnlyQuoteStore:
    return DriveOnlyQuoteStore(LocalFolderStore(folder), lambda: drive, DATASET, SETTINGS)
