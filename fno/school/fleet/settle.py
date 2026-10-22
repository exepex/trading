"""Expiry settlement before the session's first view (story MS-P1j; judge 486's note): a position whose expiry passed
has no mark in the session's capture, so a view taken before its settlement would count it at minus its maximum loss
and could trip the daily stop. Each expired position, in every driver's account and in the ticket ledger, closes at
intrinsic against NSE's archived settlement file; until that file exists it stays `settlement_needed`.

Each settlement is an `ExitRecord` (reason `expiry`) sealed with the session's decisions; its outcome is rebuilt
from the ledgers when the outcomes are sealed (`outcomes.outcomes_of`), so a rerun after the decisions' seal still
seals it. Known limit: a crash after a settlement is recorded and before the decisions' seal leaves that settlement
without an outcome record (the account itself is right); a record time on ledger entries would close it
[reasoning only]."""

from collections.abc import Iterable
from datetime import date

from ..constants import SLOT_1500, ExitReason
from ..contracts.accounts import LedgerEntry
from ..contracts.decisions import OpenPosition
from ..contracts.records import ExitRecord
from .books import Books
from .ledgers import open_positions
from .outcomes import TICKET_PREFIX


def expiry_of(position: OpenPosition) -> date:
    return min(leg.key.expiry for leg in position.legs)


def is_ticket_id(position_id: str) -> bool:
    return position_id.startswith(TICKET_PREFIX)


def settle_expired(books: Books, driver_ids: Iterable[str], session: date) -> tuple[ExitRecord, ...]:
    settled = []
    for driver_id in driver_ids:
        for reader in (books.account_entries, books.ticket_entries):
            for position in open_positions(reader.entries(driver_id)):
                if expiry_of(position) >= session:
                    continue
                if is_ticket_id(position.position_id):
                    fill = books.tickets.settle(position, expiry_of(position))
                else:
                    fill = books.fills.settle(position, expiry_of(position))
                    if fill.filled:
                        closing = LedgerEntry(position, fill, closes=True, exit_reason=ExitReason.EXPIRY)
                        books.accounts.record(driver_id, closing)
                if fill.filled:
                    settled.append(ExitRecord(session, SLOT_1500, position.position_id, driver_id, position.road,
                                              ExitReason.EXPIRY, ""))  # fmt: skip
    return tuple(settled)
