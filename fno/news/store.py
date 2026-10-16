"""Where A19's records live (story A19, scopes 4 and 6; story O9): parts and seen snapshots written once in Drive
through O9's `DataStore`, each with its SHA-256 receipt, and read back only through receipts and the verified
`DriveCache`. Nothing of an item is written to the repository."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from ..models import IST
from ..storage.data_store import DataStore
from ..storage.drive_cache import DriveCache
from ..storage.receipts import Receipt, ReceiptFolder
from .memory import SeenMemory
from .names import PARTS_FOLDER, SEEN_FOLDER

UNREADABLE = "news records in the receipts could not be read: {problems}"
SNAPSHOT_TRIES = 3


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
        """The newest readable snapshot plus every part receipted at or after it (replaying a line twice changes
        nothing); an empty memory when no news record exists yet. An unreadable snapshot falls back to the one before
        it (up to `SNAPSHOT_TRIES`); SeenSetLoadError when no snapshot or a needed part cannot be read: never a
        quietly empty memory."""
        snapshots = sorted(self._receipts(SEEN_FOLDER), key=lambda r: r.written_at, reverse=True)
        memory, since, problems = SeenMemory(), None, []
        for receipt in snapshots[:SNAPSHOT_TRIES]:
            try:
                memory, since = SeenMemory.from_dict(json.loads(self.read(receipt))), receipt.written_at
                break
            except (SeenSetLoadError, ValueError, KeyError, TypeError) as problem:
                problems.append(str(problem))
        else:
            if snapshots:
                raise SeenSetLoadError(UNREADABLE.format(problems="; ".join(problems)))
        parts = [r for r in self._receipts(PARTS_FOLDER) if since is None or r.written_at >= since]
        for receipt in sorted(parts, key=lambda r: (r.written_at, r.path)):
            for text in self.read(receipt).splitlines():
                memory.replay(json.loads(text))
        return memory

    def part_lines(self, receipts: list[Receipt]) -> list[dict]:
        return [json.loads(text) for receipt in receipts for text in self.read(receipt).splitlines()]

    def part_receipts(self) -> list[Receipt]:
        return self._receipts(PARTS_FOLDER)

    def read(self, receipt: Receipt) -> str:
        """One receipted file, verified against its SHA-256 like O9's cache does, from the cache or else from Drive;
        a missing or damaged file is SeenSetLoadError (only this file is needed, never its whole folder)."""
        local = self.cache.local(receipt.path)
        if local.is_file() and _sha256(local.read_bytes()) == receipt.sha256:
            return local.read_text(encoding="utf-8")
        data = self.cache.drive.get(receipt.path)
        if data is None or _sha256(data) != receipt.sha256:
            problem = "not returned by Drive" if data is None else "bytes do not match the receipt"
            raise SeenSetLoadError(UNREADABLE.format(problems=f"{receipt.path}: {problem}"))
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(data)
        return data.decode("utf-8")

    def _receipts(self, folder: str) -> list[Receipt]:
        return self.receipts.under(f"{self.data.area}/{folder}")

    def _path(self, folder: str, now: datetime, sequence: int, suffix: str) -> str:
        local = now.astimezone(IST)
        return f"{folder}/{local:%Y/%m/%d}/{self.data.run_id}-{sequence:04d}.{suffix}"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
