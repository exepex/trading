"""A rerun after a crash between the seal and the fills (story MS-P1j: a rerun seals nothing twice): the sealed
decisions are read back and only what the ledgers do not hold yet is filled, so no position opens or closes twice."""

from collections.abc import Iterable

from ..constants import Outcome
from ..contracts.accounts import SealedDecision
from ..contracts.records import DecisionRecord, ExitRecord
from ..tickets.book import ticket_id
from .books import Books
from .ledgers import open_positions
from .running_view import position_id


def ledger_id(record: DecisionRecord) -> str:
    """The position a sealed trade or ticket opens: `ticket:` IDs in the ticket ledger, plain IDs in the account."""
    if record.decision.outcome == Outcome.TICKET:
        return ticket_id(SealedDecision(record.decision, ""))
    return position_id(record.decision)


Todo = tuple[tuple[DecisionRecord, ...], tuple[ExitRecord, ...]]


def not_yet_filled(books: Books, driver_ids: Iterable[str], records: tuple[DecisionRecord, ...],
                   exits: tuple[ExitRecord, ...]) -> Todo:  # fmt: skip
    opened, still_open = set(), set()
    for driver_id in driver_ids:
        for reader in (books.account_entries, books.ticket_entries):
            entries = reader.entries(driver_id)
            opened |= {e.position.position_id for e in entries if not e.closes}
            still_open |= {p.position_id for p in open_positions(entries)}
    todo = tuple(r for r in records if r.decision.outcome not in (Outcome.TRADE, Outcome.TICKET)
                 or ledger_id(r) not in opened)  # fmt: skip
    return todo, tuple(e for e in exits if e.position_id in still_open)
