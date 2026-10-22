"""Model-priced snapshots for the attribution tests (story MS-INS, part b): every quote's mid is B1's Black-76 price at
a chosen forward and volatility, the bid and ask 0.05 either side, so the hand-computed values are reproducible."""

from datetime import date, datetime

from fno.constants import SIDE_BUY, SIDE_SELL
from fno.school.constants import ExitReason, OptionKind
from fno.school.contracts.accounts import FilledLeg, FillResult
from fno.school.contracts.records import OutcomeRecord
from fno.school.contracts.snapshot import ContractKey, SlotQuote, SlotSnapshot
from fno.school.instructor.attribution.greeks import price
from fno.school.instructor.attribution.points import years_left
from fno.school.instructor.contracts import HeldPath
from tests.school.contracts.builders import IST
from tests.school.instructor.builders import ROAD

EXPIRY = date(2026, 11, 23)
STRIKES = (900.0, 1000.0, 1100.0)
HALF_SPREAD, CHARGE, UNITS = 0.05, 20.0, 30
SHORT, LONG = ContractKey(EXPIRY, 1000.0, OptionKind.PUT), ContractKey(EXPIRY, 900.0, OptionKind.PUT)


def model_snapshot(day: date, forward: float, sigma: float, rate: float = 0.0, drop=()) -> SlotSnapshot:
    finished = datetime(day.year, day.month, day.day, 15, 2, tzinfo=IST)
    years = years_left(finished, EXPIRY)
    quotes = {}
    for strike in STRIKES:
        for kind in OptionKind:
            key = ContractKey(EXPIRY, strike, kind)
            if key not in drop:
                mid = price(forward, strike, kind.value, years, rate, sigma)
                half = min(HALF_SPREAD, mid / 2)  # a cheap far leg keeps a positive bid around the same mid
                quotes[key] = SlotQuote(mid - half, mid + half, 1000, 1000, mid, True)
    return SlotSnapshot(ROAD, day, f"fixture_{day:%Y%m%d}", f"{day.day:02d}" * 32, finished.replace(minute=0),
                        finished, forward, (EXPIRY,), quotes)  # fmt: skip


def touch(snapshot: SlotSnapshot, key: ContractKey, side: str) -> float:
    quote = snapshot.quote(key)
    return quote.ask if side == SIDE_BUY else quote.bid


def fills(snapshot: SlotSnapshot, closing: bool, at: datetime | None = None, prices=None) -> FillResult:
    sides = {SHORT: SIDE_BUY, LONG: SIDE_SELL} if closing else {SHORT: SIDE_SELL, LONG: SIDE_BUY}
    legs = tuple(
        FilledLeg(k, s, UNITS, prices[k] if prices else touch(snapshot, k, s), CHARGE) for k, s in sides.items()
    )
    return FillResult(legs, filled_at=at or snapshot.finished_at.replace(minute=4), rests_on="cd" * 32)


def path(snapshots: tuple[SlotSnapshot, ...], settlement: float | None = None) -> HeldPath:
    """A put spread entered on the first snapshot, closed on the last (or settled at `settlement`)."""
    entry = fills(snapshots[0], closing=False)
    if settlement is None:
        leaving, reason = fills(snapshots[-1], closing=True), ExitReason.PROFIT_TARGET
    else:
        values = {k: max(k.strike - settlement, 0.0) for k in (SHORT, LONG)}
        at = datetime(EXPIRY.year, EXPIRY.month, EXPIRY.day, 15, 30, tzinfo=IST)
        leaving, reason = fills(snapshots[-1], closing=True, at=at, prices=values), ExitReason.EXPIRY
    net = entry.cash + leaving.cash
    paid = entry.legs + (leaving.legs if settlement is None else ())
    shot = {leg: snapshots[0] if leg in entry.legs else snapshots[-1] for leg in paid}
    slippage = sum(abs(leg.price - shot[leg].quote(leg.key).mid) * leg.units for leg in paid)
    record = OutcomeRecord("p1", "CS1@1", ROAD, "cd" * 32, entry, leaving, reason, net + 4 * CHARGE, 4 * CHARGE, net,
                           net / 2500.0, slippage)  # fmt: skip
    return HeldPath(record, None, None, snapshots, settlement, 0, ())
