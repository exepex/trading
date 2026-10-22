"""The recorded-day fixture builder (story MS-P1i): one session of all five roads, each capture holding two expiries,
and the drivers that trade, do not, or would be refused. Snapshots start inside every road's recorder window (15:01 to
15:10 is inside all five), unlike a's contract builders, which start at 15:00:00. Fixed values only: no live data."""

from dataclasses import replace
from datetime import date, timedelta

from fno.school.acceptance.scenario import DriverPlan, Scenario
from fno.school.constants import OptionKind, RoadCode
from fno.school.contracts.roads import ROADS
from fno.school.contracts.snapshot import ContractKey, SlotSnapshot
from tests.school.contracts import builders as b

STARTED = b.SLOT_AT + timedelta(minutes=2)  # 15:02
FILL_AT = b.SLOT_AT + timedelta(minutes=6)  # 15:06, after the snapshots end (15:04) and the seal (15:05)
SEAL_PUSHED_AT = b.SLOT_AT + timedelta(minutes=5)
CAP_RS = 10_000
LATER_EXPIRY = date(2026, 12, 28)
EXPIRIES = (b.EXPIRY, LATER_EXPIRY)
LOT_UNITS = 30


PUT_QUOTES = {800.0: (1.0, 2.0), 900.0: (4.0, 5.0), 1000.0: (10.0, 11.0), 1100.0: (25.0, 26.0), 1200.0: (60.0, 61.0)}


def recorded_snapshot(code: RoadCode) -> SlotSnapshot:
    """Five put strikes on two expiries, no vertical impossible; 900 and 1000 are the contracts' fixture legs."""
    quotes = {
        ContractKey(expiry, strike, OptionKind.PUT): b.quote(bid, ask)
        for expiry in EXPIRIES
        for strike, (bid, ask) in PUT_QUOTES.items()
    }
    return replace(b.snapshot(code), snapshot_id=f"{code}_20261102_150200", started_at=STARTED,
                   finished_at=STARTED + timedelta(minutes=2), expiries=EXPIRIES, quotes=quotes)  # fmt: skip


def recorded_day() -> Scenario:
    """All five roads open; CS1 and DR1 trade on each, N0 never does."""
    codes = [road.code for road in ROADS]
    return Scenario(
        session=b.SESSION,
        snapshots={code: recorded_snapshot(code) for code in codes},
        listed_expiries=dict.fromkeys(codes, EXPIRIES),
        lots={code: dict.fromkeys(EXPIRIES, LOT_UNITS) for code in codes},
        drivers=(
            DriverPlan(b.card("CS1"), b.put_spread()),
            DriverPlan(b.card("DR1"), b.put_spread(max_loss=1800.0)),
            DriverPlan(b.card("N0")),
        ),
        cap_rs=CAP_RS,
        fill_at=FILL_AT,
        seal_pushed_at=SEAL_PUSHED_AT,
    )
