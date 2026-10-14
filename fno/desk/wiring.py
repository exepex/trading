"""Composition root of the paper desk's fills and exits (story E4): the only place that picks the quote store the
execution snapshots are read from, the charges model's table, the alert sender and the account writer. Swapping any of
them changes this file only. Nothing here can place an order: the desk reads recorded quotes, never a broker."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ..books.lock import DEFAULT_LEASE_SECONDS
from ..composition import build_alert_sender, open_account_writer
from ..config import ROOT
from ..storage.wiring import build_quote_store
from .entries import EntryDesk
from .exits import ExitDesk
from .records import DeskJournal
from .snapshot import ExecutionSnapshotSource, RecordedExecutionSnapshots


def build_execution_snapshots(folder: Path | None = None) -> ExecutionSnapshotSource:
    """A4's recorded captures (the repository's quote folder), read by snapshot ID."""
    return RecordedExecutionSnapshots(build_quote_store(folder))


def build_entry_desk(cfg: dict) -> EntryDesk:
    return EntryDesk(cfg["charges"])


def build_exit_desk(cfg: dict) -> ExitDesk:
    return ExitDesk(cfg["charges"], build_alert_sender())


@contextmanager
def open_desk_journal(
    book: str, root: Path = ROOT, lease_seconds: float = DEFAULT_LEASE_SECONDS
) -> Iterator[DeskJournal]:
    """The book's desk journal under its single-writer lock (E1): `AccountBusy` if another writer holds it."""
    with open_account_writer(book, root, lease_seconds) as writer:
        yield DeskJournal(writer)
