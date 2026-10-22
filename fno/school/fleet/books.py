"""The two ledgers the fleet writes (story MS-P1j): the driver accounts (MS-P1d) and the ticket ledger (MS-P1f), each
with its read-only entries, and the one fill port both are filled through."""

from collections.abc import Callable
from dataclasses import dataclass

from ..contracts.accounts import AccountPort, FillPort, LedgerReader
from ..contracts.decisions import OpenPosition
from ..contracts.snapshot import ContractKey
from ..tickets.book import TicketBook

EntryMids = Callable[[OpenPosition], dict[ContractKey, float]]  # the mids an entry met, from its sealed record


@dataclass(frozen=True)
class Books:
    accounts: AccountPort
    account_entries: LedgerReader
    tickets: TicketBook
    ticket_entries: LedgerReader
    fills: FillPort
