"""One Drive data file read by its own receipt and verified against its SHA-256 (story FL1-1e). O9's
`DriveCache.sync` brings a whole folder: given one file's path it matches no receipt and reports nothing, which hid
that the evening never read A4h's close (22-23 Oct 2026). So the lab reads a single file here: no receipt means the
file is not out yet (None); a receipt whose file Drive does not return, or returns with other bytes, is a problem
(`Unverified`), never a value."""

from __future__ import annotations

import hashlib

from ..storage.raw_store import RawFileStore
from ..storage.receipts import ReceiptFolder

MISSING, DAMAGED = "missing", "damaged"


class Unverified(RuntimeError):
    def __init__(self, path: str, problem: str):
        super().__init__(f"{path}: {problem}")
        self.problem = problem


class VerifiedFiles:
    def __init__(self, drive: RawFileStore, receipts: ReceiptFolder):
        """`drive`: the whole project folder (paths include the area), as O9's cache and data store hold it."""
        self.drive, self.receipts = drive, receipts

    def read(self, path: str) -> bytes | None:
        """The file's bytes, verified; None when it has no receipt yet."""
        receipt = self.receipts.read(path)
        if receipt is None:
            return None
        data = self.drive.get(path)
        if data is None:
            raise Unverified(path, MISSING)
        if hashlib.sha256(data).hexdigest() != receipt.sha256:
            raise Unverified(path, DAMAGED)
        return data
