"""The day's packs as one step (stories E2 and E3): the common market pack and each packed book's private pack, built
and written once. `desk pack` and the daily run both use it. The common pack is refused (PackError) while the day's
canonical A4 snapshot is not committed, so the daily run pulls first and retries until the recorder's window ends.
A book's private pack holds its account folder's text, so it is kept privately (`keep`: Drive, story E2c) and only its
`.sha256` file is committed beside the common pack."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date, time
from pathlib import Path

from .common_pack import CommonPack, CommonPackBuilder
from .daily_ports import Packs
from .pack_store import PackStore
from .private_pack import PrivatePackBuilder


class WrittenPacks(Packs):
    def __init__(self, common: CommonPackBuilder, private: PrivatePackBuilder, store: PackStore, cutoff: time,
                 books: Sequence[str], refresh: Callable[[], None] = lambda: None,
                 keep: Callable[[list[Path]], None] = lambda paths: None):  # fmt: skip
        self.common, self.private, self.store, self.cutoff = common, private, store, cutoff
        self.books, self.refresh = tuple(books), refresh  # refresh: pull, so another container's snapshot is seen
        self.keep = keep  # keep(paths): the private packs, kept out of the public record

    def build(self, day: date) -> CommonPack:
        self.refresh()
        pack = self.common.build(day, self.cutoff)
        self.store.write_common(pack)
        for book in self.books:
            self.store.write_private(self.private.build(book, day))
        self.keep([self.store.private_path(book, day) for book in self.books])
        return pack

    def written(self, day: date) -> list[tuple[Path, str]]:
        """Each written pack file of the day with its SHA-256 (from its `.sha256` file)."""
        paths = [self.store.common_path(day), *(self.store.private_path(book, day) for book in self.books)]
        return [(p, p.with_suffix(".sha256").read_text(encoding="utf-8").split()[0]) for p in paths if p.is_file()]

    def stored(self, day: date) -> CommonPack | None:
        path = self.store.common_path(day)
        return CommonPack.read(day, path) if path.is_file() else None

    def files(self, day: date) -> tuple[Path, ...]:
        """What the pack step commits: the common pack, and every pack's `.sha256` (a private pack's text is kept)."""
        common = self.store.common_path(day)
        sums = tuple(written.with_suffix(".sha256") for written, _ in self.written(day))
        return ((common,) if common.is_file() else ()) + sums
