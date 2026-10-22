"""Plain fakes and fixed records for the sections' tests (story MS-P1g). Strikes and prices are planted on purpose,
so the privacy test can prove none of them reaches a section."""

from dataclasses import dataclass, field, replace
from datetime import date

from fno.school.constants import ClosureReason, DriverRole, Outcome, RefusalReason, RoadCode
from fno.school.contracts.decisions import Decision
from fno.school.contracts.records import DecisionRecord, OutcomeRecord
from fno.school.contracts.roads import ROADS, ROADS_BY_CODE, RoadDay, RoadStatus
from fno.school.contracts.tickets import OpportunityCounts
from fno.school.reports.inputs import PlannedTrade
from tests.school.contracts import builders as b
from tests.school.contracts.test_records import closed_record, outcome_record, trade_record

SESSION = b.SESSION
ROLES = {"CS1@1": DriverRole.RULE, "N0@1": DriverRole.CONTROL, "PS5@1": DriverRole.MEASUREMENT_ONLY}


def open_roads() -> tuple[RoadDay, ...]:
    return tuple(b.road_day(road.code) for road in ROADS)


def roads_with_one_closed(code=RoadCode.FINNIFTY_MONTHLY, reason=ClosureReason.LOT_MISMATCH) -> tuple[RoadDay, ...]:
    days = [b.road_day(road.code) for road in ROADS if road.code is not code]
    return (*days, RoadDay(ROADS_BY_CODE[code], SESSION, (), None, None, RoadStatus(reason)))


def plan(driver="CS1@1", role=DriverRole.RULE, loss=2500.0) -> PlannedTrade:
    return PlannedTrade(driver, role, RoadCode.BANKNIFTY_MONTHLY, "PCS", loss)


def refused_record(reason=RefusalReason.MAX_LOSS) -> DecisionRecord:
    decision = Decision("CS1@1", RoadCode.NIFTY_MONTHLY, SESSION, Outcome.REFUSED, reason, b.put_spread())
    return replace(trade_record(), road=RoadCode.NIFTY_MONTHLY, decision=decision)


def net_record(driver="CS1@1", net=137.7, ticket=False) -> OutcomeRecord:
    return replace(outcome_record(), driver_id=driver, net=net, is_ticket=ticket)


@dataclass
class Today:
    days: tuple[RoadDay, ...] = field(default_factory=open_roads)
    trades: tuple[PlannedTrade, ...] = field(default_factory=lambda: (plan(),))

    def roads(self, session):
        return self.days

    def plan(self, session):
        return self.trades


@dataclass
class Day:
    items: tuple = ()
    rows: tuple = ()

    def records(self, session):
        return self.items

    def counts(self, session):
        return self.rows

    def role_of(self, driver_id):
        return ROLES[driver_id]


def counts(driver="CS1@1", eligible=3, fillable=2, executed=1) -> OpportunityCounts:
    return OpportunityCounts(SESSION, RoadCode.BANKNIFTY_MONTHLY, driver, eligible, fillable, executed)


__all__ = ["closed_record", "date"]
