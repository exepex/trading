"""Gets a raw file from the cheapest place that has it: the stores first, then the original source, and keeps a
copy of anything fetched. Knows only the two interfaces, never a concrete store or source."""

from __future__ import annotations

from dataclasses import dataclass

from .raw_source import RawFileSource
from .raw_store import RawFileStore


@dataclass(frozen=True)
class RawFile:
    data: bytes | None  # None: the source does not publish this file
    origin: str  # the store or source it came from


class RawFileLibrary:
    def __init__(self, stores: list[RawFileStore], source: RawFileSource, archive: RawFileStore | None = None):
        self.stores, self.source, self.archive = stores, source, archive

    def get(self, filename: str) -> RawFile:
        for store in self.stores:
            data = store.get(filename)
            if data is not None:
                return RawFile(data, store.name)
        data = self.source.fetch(filename)
        if data is not None and self.archive is not None:
            self.archive.put(filename, data)
        return RawFile(data, self.source.name)
