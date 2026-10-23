"""Real O9 parts for the lab's single-file reads (FL1-1e): a local Drive folder, the receipts written by O9's own
`DataStore`, read through `VerifiedFiles`. A fake cache that accepted a file's path hid the 22-23 Oct bug."""

from fno.forecast_lab.verified_file import VerifiedFiles
from fno.storage.data_store import DataStore
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipts import ReceiptFolder


class DriveFiles:
    def __init__(self, tmp_path):
        self.drive, self.receipts = LocalFolderStore(tmp_path / "drive"), ReceiptFolder(tmp_path / "receipts")
        self.store = DataStore(self.drive, "data", self.receipts, "test", "run-1")
        self.files = VerifiedFiles(self.drive, self.receipts)

    def put(self, path: str, data: bytes) -> None:
        """`path`: the Drive path, area included (`data/...`); written with its receipt."""
        self.store.put(path.removeprefix("data/"), data)

    def damage(self, path: str) -> None:
        self.drive.folder.joinpath(path).write_bytes(b"tampered")

    def lose(self, path: str) -> None:
        self.drive.folder.joinpath(path).unlink()
