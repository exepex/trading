"""A small archived history for the source tests. Fixed values only."""

from datetime import date, timedelta
from pathlib import Path

import yaml

from fno.research_data.calendar import CsvSessionCalendar
from fno.school.constants import OptionKind
from fno.school.contracts.roads import ROADS_BY_CODE
from fno.school.simulator.constants import MIN_QUOTED_SESSIONS
from fno.school.simulator.history import edge1
from fno.school.simulator.history.ports import ChainRow, DayChain
from fno.school.simulator.spreads.bucket import bucket_of
from fno.school.simulator.spreads.model import SpreadModel
from fno.school.simulator.terms import DatedTerms

SESSION = date(2022, 3, 7)  # a Monday inside every window
MONTHLIES = (date(2022, 3, 31), date(2022, 4, 28))
WEEKLIES = (date(2022, 3, 10), date(2022, 3, 17))
HOLIDAY = date(2022, 3, 8)
SPOT = 17000.0
CHARGES = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))["charges"]
TERMS = DatedTerms(edge1.circular_lot_or_none, edge1.dated_charges(CHARGES))
CALENDAR = CsvSessionCalendar(
    f"date,kind,description,source_url\n{HOLIDAY},holiday,test holiday,https://example.test/circular\n"
)


def close_of(strike: float, kind: OptionKind, spot: float = SPOT) -> float:
    intrinsic = max(spot - strike, 0.0) if kind is OptionKind.CALL else max(strike - spot, 0.0)
    return round(intrinsic + 100.0 * 0.9 ** (abs(strike - spot) / 100), 2)


def rows(expiries, monthly: bool, strikes=None, volume: int = 10) -> list[ChainRow]:
    strikes = strikes or [SPOT + 100.0 * n for n in range(-5, 6)]
    return [
        ChainRow(e, s, k, close_of(s, k), volume, 1000, monthly) for e in expiries for s in strikes for k in OptionKind
    ]


def chain(underlying="NIFTY", session=SESSION, monthly=True, **kwargs) -> DayChain:
    both = rows(MONTHLIES, True, **kwargs) + rows(WEEKLIES, False, **kwargs)
    return DayChain(session, underlying, SPOT, tuple(both), {}, "legacy")


class DictChain:
    """A `HistoricalChain` over fixed days that records every day it is asked for."""

    def __init__(self, *days: DayChain):
        self.days, self.asked = {(d.underlying, d.session): d for d in days}, []

    def day(self, underlying, session):
        self.asked.append((underlying, session))
        return self.days.get((underlying, session))


def full_model(road_code, scenario_gap: float = 0.01, session: date = SESSION) -> SpreadModel:
    """Every bucket of the road holds 30 quoted sessions, each at `scenario_gap`: the model has no gaps."""
    underlying = ROADS_BY_CODE[road_code].underlying
    buckets = {
        bucket_of(underlying, SPOT, SPOT + 100.0 * n, session, e) for n in range(-5, 6) for e in (*MONTHLIES, *WEEKLIES)
    }
    days = {session - timedelta(days=i): scenario_gap for i in range(MIN_QUOTED_SESSIONS)}
    return SpreadModel({b: days for b in buckets if b})
