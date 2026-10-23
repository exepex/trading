"""The fired entries that never filled (story MS-P1j, for MS-INS part e's paired comparison): every sealed trade or
ticket decision whose position its ledger never opened, whatever the reason (the shared size, a refused fill, a stale
seal). No fill status is stored, so it is derived from the dashcam and the two ledgers, read-only."""

from datetime import date, timedelta

from ..constants import SLOT_1500, Outcome, RecordKind, RoadCode
from ..contracts.accounts import LedgerReader
from ..contracts.dashcam import DashcamStore
from ..contracts.records import DecisionRecord
from .ledgers import ledger_id

SlotKey = tuple[str, RoadCode, date]  # (driver ID, road, entry session): MS-INS's key


class UnfilledEntries:
    def __init__(self, dashcam: DashcamStore, account_entries: LedgerReader, ticket_entries: LedgerReader):
        self.dashcam, self.readers = dashcam, (account_entries, ticket_entries)

    def __call__(self, first: date, last: date) -> frozenset[SlotKey]:
        opened: dict[str, set[str]] = {}
        unfilled = set()
        for record in self._fired(first, last):
            driver_id = record.decision.driver_id
            if driver_id not in opened:
                # every ID a ledger holds was opened there (a close needs its opening, d's position book refuses one)
                opened[driver_id] = {
                    e.position.position_id for reader in self.readers for e in reader.entries(driver_id)
                }
            if ledger_id(record) not in opened[driver_id]:
                unfilled.add((driver_id, record.road, record.session))
        return frozenset(unfilled)

    def _fired(self, first: date, last: date):
        day = first
        while day <= last:
            seal = self.dashcam.find(day, SLOT_1500, RecordKind.DECISIONS)
            for record in self.dashcam.read(seal) if seal is not None else ():
                if isinstance(record, DecisionRecord) and record.decision.outcome in (Outcome.TRADE, Outcome.TICKET):
                    yield record
            day += timedelta(days=1)
