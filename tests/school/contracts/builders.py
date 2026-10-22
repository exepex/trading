"""Small valid school objects for tests (story MS-P1a). Fixed values only: no live strike, price or capture."""

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

from fno.constants import SIDE_BUY, SIDE_SELL
from fno.school.constants import DriverRole, OptionKind, Outcome, RoadCode
from fno.school.contracts.accounts import FilledLeg, FillResult, LedgerEntry, SealedDecision
from fno.school.contracts.decisions import Decision, DriverCard, LegSpec, OpenPosition, Proposal
from fno.school.contracts.roads import OPEN, ROADS_BY_CODE, DatedLot, RoadDay, RoadStatus
from fno.school.contracts.safety import AccountView
from fno.school.contracts.seal import Seal
from fno.school.contracts.snapshot import ContractKey, SlotQuote, SlotSnapshot

IST = timezone(timedelta(hours=5, minutes=30))
SESSION = date(2026, 11, 2)
EXPIRY = date(2026, 11, 23)
SLOT_AT = datetime(2026, 11, 2, 15, 0, tzinfo=IST)


def key(strike: float, kind: OptionKind = OptionKind.PUT) -> ContractKey:
    return ContractKey(EXPIRY, strike, kind)


def quote(bid: float = 10.0, ask: float = 11.0, size: int = 1000) -> SlotQuote:
    return SlotQuote(bid, ask, size, size, (bid + ask) / 2, True)


def road_day(code: RoadCode = RoadCode.BANKNIFTY_MONTHLY, status: RoadStatus = OPEN) -> RoadDay:
    lot = DatedLot(30, "fixture") if status.open else None
    step = 100.0 if status.open else None
    steps = {EXPIRY: step} if status.open else {}
    return RoadDay(ROADS_BY_CODE[code], SESSION, (EXPIRY,) if status.open else (), lot, step, status, steps)


def snapshot(code: RoadCode = RoadCode.BANKNIFTY_MONTHLY, quotes: dict | None = None) -> SlotSnapshot:
    quotes = {key(1000.0): quote(), key(900.0): quote(4.0, 5.0)} if quotes is None else quotes
    return SlotSnapshot(code, SESSION, "fixture_20261102_150100", "ab" * 32, SLOT_AT, SLOT_AT + timedelta(minutes=2),
                        1050.0, (EXPIRY,), quotes)  # fmt: skip


def put_spread(max_loss: float = 2500.0) -> Proposal:
    legs = (LegSpec(key(1000.0), SIDE_SELL, 1), LegSpec(key(900.0), SIDE_BUY, 1))
    return Proposal("PCS", legs, 30, 180.0, max_loss, 85.0, 0.5)


def proposal_with(**changes) -> Proposal:
    return replace(put_spread(), **changes)


def card(code: str = "CS1", role: DriverRole = DriverRole.RULE) -> DriverCard:
    return DriverCard(code, "1", "capped_seller", role, (RoadCode.BANKNIFTY_MONTHLY,), 10, {"dte_min": 20})


def seal(pushed_at: datetime = SLOT_AT + timedelta(minutes=3), sha256: str = "cd" * 32) -> Seal:
    return Seal("school/dashcam/2026/11/02/1500.jsonl.gz", sha256, pushed_at, "abc1234")


def account(driver_id: str = "CS1@1") -> AccountView:
    return AccountView(driver_id, 2_000_000.0, 2_000_000.0, 2_000_000.0, 2_000_000.0, 0.0, (), (), None, None)


def decision(driver_id: str = "CS1@1") -> Decision:
    return Decision(driver_id, RoadCode.BANKNIFTY_MONTHLY, SESSION, Outcome.TRADE, "", put_spread())


def sealed(file_sha256: str = "cd" * 32) -> SealedDecision:
    return SealedDecision(decision(), file_sha256)


def position(position_id: str = "p1", driver_id: str = "CS1@1") -> OpenPosition:
    spread = put_spread()
    return OpenPosition(position_id, driver_id, RoadCode.BANKNIFTY_MONTHLY, "PCS", spread.legs, 30, SESSION, 95.0,
                        spread.max_loss)  # fmt: skip


def filled(at: datetime = SLOT_AT + timedelta(minutes=4)) -> FillResult:
    return FillResult((FilledLeg(key(1000.0), SIDE_SELL, 30, 10.0, 21.4),), filled_at=at, rests_on="cd" * 32)


def opening(position_id: str = "p1") -> LedgerEntry:
    return LedgerEntry(position(position_id), filled(), closes=False)
