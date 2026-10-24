"""What the replay clock may see of the real Drive record (story REH1: no look-ahead). A file with an O9 receipt is
visible once its receipt's `written_at` is at or before the replay clock's now. The paper accounts' private files have
no receipts (they are index files, replaced in place): they are read as they are now, the one stated limit. Any other
file without a receipt was never recorded as of the replay, so it is not visible."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from ..storage.receipts import ReceiptFolder

STATE_AREAS = ("paper/",)  # the private records E2c keeps in Drive (index files, no history)


class Visibility:
    def __init__(self, receipts: ReceiptFolder, now: Callable[[], datetime]):
        self.receipts, self.now = receipts, now

    def __call__(self, path: str) -> bool:
        if path.startswith(STATE_AREAS):
            return True
        receipt = self.receipts.read(path)
        return receipt is not None and datetime.fromisoformat(receipt.written_at) <= self.now()
