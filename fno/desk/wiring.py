"""Composition root of the paper desk's fills, exits and settlements (stories E4 and E7): the only place that picks
the quote store the execution snapshots are read from, the charges model's table, the alert sender, NSE's final
settlement prices and the account writer. Swapping any of them changes this file only. Nothing here can place an
order: the desk reads recorded quotes and published NSE files, never a broker."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ..books.lock import DEFAULT_LEASE_SECONDS
from ..composition import build_alert_sender, open_account_writer
from ..config import ROOT
from ..storage.wiring import build_nse_fo_library, build_quote_store
from .entries import EntryDesk
from .exits import ExitDesk
from .records import DeskJournal
from .settlement import NseFinalSettlement
from .snapshot import ExecutionSnapshotSource, RecordedExecutionSnapshots


def build_execution_snapshots(folder: Path | None = None) -> ExecutionSnapshotSource:
    """A4's recorded captures (the repository's quote folder), read by snapshot ID."""
    return RecordedExecutionSnapshots(build_quote_store(folder))


def build_entry_desk(cfg: dict) -> EntryDesk:
    return EntryDesk(cfg["charges"])


def build_exit_desk(cfg: dict) -> ExitDesk:
    """Exits at the execution snapshot's quotes; expired legs settled from NSE's daily F&O files (A2's library)."""
    return ExitDesk(cfg["charges"], build_alert_sender(), NseFinalSettlement(build_nse_fo_library()))


@contextmanager
def open_desk_journal(
    book: str, root: Path = ROOT, lease_seconds: float = DEFAULT_LEASE_SECONDS
) -> Iterator[DeskJournal]:
    """The book's desk journal under its single-writer lock (E1): `AccountBusy` if another writer holds it."""
    with open_account_writer(book, root, lease_seconds) as writer:
        yield DeskJournal(writer)
