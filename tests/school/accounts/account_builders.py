"""Accounts for the MS-P1d tests: a real `SchoolAccounts` on a temporary root, entries made by the real fill port."""

from dataclasses import dataclass, field, replace
from datetime import date, timedelta

from fno.school.accounts.school_accounts import SchoolAccounts
from fno.school.constants import ExitReason, RoadCode
from fno.school.contracts.accounts import LedgerEntry, SealedDecision
from fno.school.contracts.decisions import OpenPosition
from tests.school.contracts import builders as b
from tests.school.execution.school_builders import AT, CHARGES, fills

ACCOUNT_RS, BRAKE_RS = 2_000_000.0, 120_000.0
NEXT = b.SESSION + timedelta(days=1)


@dataclass
class Reviews:
    rows: dict[str, list[date]] = field(default_factory=dict)

    def lifts(self, driver_id: str, before: date) -> tuple[date, ...]:
        return tuple(sorted(day for day in self.rows.get(driver_id, []) if day < before))


@dataclass
class Sync:
    pulled: list = field(default_factory=list)
    pushed: list = field(default_factory=list)

    def pull(self, paths):
        self.pulled.append([p.name for p in paths])

    def push(self, paths):
        self.pushed.append([p.name for p in paths])


def accounts(tmp_path, reviews: Reviews | None = None, sync: Sync | None = None) -> SchoolAccounts:
    return SchoolAccounts(tmp_path, ACCOUNT_RS, BRAKE_RS, CHARGES, reviews or Reviews(), sync)


def position(position_id: str = "p1", lots: int = 1, opened: date = b.SESSION) -> OpenPosition:
    legs = tuple(replace(leg, lots=lots) for leg in b.put_spread().legs)
    return replace(b.position(position_id), legs=legs, opened=opened)


def opening(tmp_path, position_id: str = "p1", lots: int = 1) -> LedgerEntry:
    held = position(position_id, lots)
    proposal = replace(b.put_spread(), legs=held.legs)
    sealed = SealedDecision(replace(b.decision(), proposal=proposal), "cd" * 32)
    big = {k: b.quote(q.bid, q.ask, size=100_000) for k, q in b.snapshot().quotes.items()}
    return LedgerEntry(held, fills(tmp_path).enter(sealed, b.snapshot(quotes=big), b.seal(), AT), closes=False)


def closing(tmp_path, entry: LedgerEntry, quotes: dict | None = None) -> LedgerEntry:
    snapshot = b.snapshot(quotes=quotes)
    fill = fills(tmp_path).exit(entry.position, snapshot, "cd" * 32, b.seal(), AT)
    return LedgerEntry(entry.position, fill, closes=True, exit_reason=ExitReason.PROFIT_TARGET)


def marks(quotes: dict | None = None, session: date = b.SESSION) -> dict:
    snapshot = b.snapshot(quotes=quotes)
    if session != b.SESSION:
        shift = timedelta(days=(session - b.SESSION).days)
        snapshot = replace(snapshot, session=session, started_at=snapshot.started_at + shift,
                           finished_at=snapshot.finished_at + shift)  # fmt: skip
    return {RoadCode.BANKNIFTY_MONTHLY: snapshot}


def spread_quotes(short_mid: float, long_mid: float) -> dict:
    """The fixture's two puts at these mids (half a rupee each side), deep sizes."""
    return {b.key(1000.0): b.quote(short_mid - 0.5, short_mid + 0.5, 100_000),
            b.key(900.0): b.quote(long_mid - 0.5, long_mid + 0.5, 100_000)}  # fmt: skip
