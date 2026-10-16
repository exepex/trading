"""Where A19's records live (story A19, scopes 4 and 6; story O9): parts and seen snapshots written once in Drive
through O9's `DataStore`, each with its SHA-256 receipt, and read back only through receipts and the verified
`DriveCache`. Nothing of an item is written to the repository."""

from __future__ import annotations

import json
from datetime import datetime

from ..models import IST
from ..storage.data_store import DataStore
from ..storage.drive_cache import DriveCache
from ..storage.receipts import Receipt, ReceiptFolder
from .memory import SeenMemory
from .names import PARTS_FOLDER, SEEN_FOLDER

UNREADABLE = "news records in the receipts could not be read: {problems}"


class SeenSetLoadError(RuntimeError):
    pass


class NewsStore:
    def __init__(self, data: DataStore, receipts: ReceiptFolder, cache: DriveCache):
        self.data, self.receipts, self.cache = data, receipts, cache

    def put_part(self, now: datetime, sequence: int, lines: list[dict]) -> Receipt:
        body = "".join(json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n" for line in lines)
        return self.data.put(self._path(PARTS_FOLDER, now, sequence, "jsonl"), body.encode("utf-8"))

    def put_snapshot(self, now: datetime, sequence: int, memory: SeenMemory) -> Receipt:
        body = json.dumps(memory.to_dict(), ensure_ascii=False, sort_keys=True)
        return self.data.put(self._path(SEEN_FOLDER, now, sequence, "json"), body.encode("utf-8"))

    def has_records(self) -> bool:
        return bool(self._receipts(PARTS_FOLDER) or self._receipts(SEEN_FOLDER))

    def load_memory(self) -> SeenMemory:
        """The newest snapshot plus every part receipted at or after it (replaying a line twice changes nothing); an
        empty memory when no news record exists yet.
        SeenSetLoadError when receipts exist but their files cannot be read: never a quietly empty memory."""
        snapshots = self._receipts(SEEN_FOLDER)
        newest = max(snapshots, key=lambda r: r.written_at) if snapshots else None
        memory = SeenMemory.from_dict(json.loads(self.read(newest))) if newest else SeenMemory()
        parts = [r for r in self._receipts(PARTS_FOLDER) if newest is None or r.written_at >= newest.written_at]
        for receipt in sorted(parts, key=lambda r: (r.written_at, r.path)):
            for text in self.read(receipt).splitlines():
                memory.replay(json.loads(text))
        return memory

    def part_lines(self, receipts: list[Receipt]) -> list[dict]:
        return [json.loads(text) for receipt in receipts for text in self.read(receipt).splitlines()]

    def part_receipts(self) -> list[Receipt]:
        return self._receipts(PARTS_FOLDER)

    def read(self, receipt: Receipt) -> str:
        folder = receipt.path.rsplit("/", 1)[0]
        report = self.cache.sync(folder)
        if not report.complete:
            raise SeenSetLoadError(UNREADABLE.format(problems="; ".join(report.problems)))
        return self.cache.local(receipt.path).read_text(encoding="utf-8")

    def _receipts(self, folder: str) -> list[Receipt]:
        return self.receipts.under(f"{self.data.area}/{folder}")

    def _path(self, folder: str, now: datetime, sequence: int, suffix: str) -> str:
        local = now.astimezone(IST)
        return f"{folder}/{local:%Y/%m/%d}/{self.data.run_id}-{sequence:04d}.{suffix}"
