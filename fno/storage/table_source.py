"""Where a reader gets a whole CSV table's text (story O9b step 2): one port, so the composition root picks the place.
`FileTable` reads a local file (tests, and a table still in the repository); `ReceiptedTable` reads a receipt-backed
Drive series through the verified cache, built on first use so missing Drive settings refuse the read, never the
wiring. Either one raises `TableUnavailable` for a table that cannot be read, naming the error type only (a message
can hold paths), and readers turn it into their own refusal (fail closed; no fallback store, owner 23 Oct 2026)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path

from .receipted_rows import ReceiptedRowLog

MISSING = "{name} is missing"
UNREADABLE = "{name}: its Drive copy could not be read ({error})"


class TableUnavailable(RuntimeError):
    """The table could not be read; the message names the table and why."""


class TableSource(ABC):
    name: str

    @abstractmethod
    def text(self) -> str:
        """The table's whole CSV text, header first; TableUnavailable when it cannot be read."""


class FileTable(TableSource):
    def __init__(self, path: Path):
        self.path, self.name = Path(path), Path(path).name

    def text(self) -> str:
        if not self.path.is_file():
            raise TableUnavailable(MISSING.format(name=self.name))
        return self.path.read_text(encoding="utf-8")


class ReceiptedTable(TableSource):
    def __init__(self, series: Callable[[], ReceiptedRowLog], name: str):
        """`series`: builds the Drive series when the table is first read."""
        self.series, self.name = series, name

    def text(self) -> str:
        try:
            data = self.series().current_bytes()
        except (RuntimeError, OSError) as error:  # settings missing, a copy unverified, sign-in, Drive's network
            raise TableUnavailable(UNREADABLE.format(name=self.name, error=type(error).__name__)) from None
        if not data:
            raise TableUnavailable(MISSING.format(name=self.name))
        return data.decode("utf-8")
