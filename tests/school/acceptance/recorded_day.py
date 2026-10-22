"""The recorded-day fixture builder (story MS-P1i): one session of all five roads with their snapshots, and the
drivers that trade, do not, or would be refused. Snapshots start inside every road's recorder window (15:01-15:10 is
inside all five), unlike a's contract builders, which start at 15:00:00. Fixed values only: no live strike or price."""

from dataclasses import replace
from datetime import timedelta

from fno.school.acceptance.scenario import DriverPlan, Scenario
from fno.school.constants import RoadCode
from fno.school.contracts.roads import ROADS
from tests.school.contracts import builders as b

STARTED = b.SLOT_AT + timedelta(minutes=2)  # 15:02
FILL_AT = b.SLOT_AT + timedelta(minutes=6)  # 15:06, after the snapshots end (15:04) and the seal (15:05)
SEAL_PUSHED_AT = b.SLOT_AT + timedelta(minutes=5)
CAP_RS = 10_000


def recorded_snapshot(code: RoadCode):
    return replace(b.snapshot(code), snapshot_id=f"{code}_20261102_150200", started_at=STARTED,
                   finished_at=STARTED + timedelta(minutes=2))  # fmt: skip


def recorded_day() -> Scenario:
    """All five roads open; CS1 and DR1 trade on each, N0 never does."""
    return Scenario(
        session=b.SESSION,
        road_days=tuple(b.road_day(road.code) for road in ROADS),
        snapshots={road.code: recorded_snapshot(road.code) for road in ROADS},
        drivers=(
            DriverPlan(b.card("CS1"), b.put_spread()),
            DriverPlan(b.card("DR1"), b.put_spread(max_loss=1800.0)),
            DriverPlan(b.card("N0")),
        ),
        cap_rs=CAP_RS,
        fill_at=FILL_AT,
        seal_pushed_at=SEAL_PUSHED_AT,
    )
