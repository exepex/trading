"""Fixtures for the driver tests (story MS-P1e): a Black-Scholes chain with a two-sided touch, a road day, spot
histories and the cards' own drivers. Fixed numbers only; no recorded quote."""

import math
from datetime import date, timedelta
from pathlib import Path

from fno.risk.trade_costs import SimulatorTradeCosts
from fno.school.constants import OptionKind, RoadCode
from fno.school.contracts.decisions import OpenPosition, SpotPoint
from fno.school.contracts.roads import OPEN, ROADS_BY_CODE, DatedLot, RoadDay
from fno.school.contracts.snapshot import ContractKey, SlotQuote, SlotSnapshot
from fno.school.drivers.cards import CARDS_FOLDER, load_cards
from fno.school.drivers.proposals import ProposalBuilder
from fno.school.drivers.wiring import build_drivers
from tests.risk.builders import ZERO_CHARGES
from tests.school.contracts.builders import SLOT_AT

ROOT = Path(__file__).resolve().parents[3]
SESSION = date(2026, 11, 2)  # a Monday
CAP = 10_000.0
SPOT = 50_000.0
VOL = 0.15


class Weekdays:
    """A calendar whose sessions are Monday to Friday."""

    def is_trading_day(self, day: date) -> bool:
        return day.weekday() < 5


CALENDAR = Weekdays()
BUILDER = ProposalBuilder(SimulatorTradeCosts(ZERO_CHARGES), CAP)


def _normal_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def option_mid(spot: float, strike: float, kind: OptionKind, days: int, vol: float = VOL) -> float:
    t = max(days, 0.2) / 365
    d1 = (math.log(spot / strike) + 0.5 * vol * vol * t) / (vol * math.sqrt(t))
    call = spot * _normal_cdf(d1) - strike * _normal_cdf(d1 - vol * math.sqrt(t))
    return call if kind == OptionKind.CALL else call - spot + strike


def chain(
    spot: float,
    step: float,
    session: date,
    expiries: tuple[date, ...],
    span: int = 60,
    vol: float = VOL,
    spread: float = 0.002,
) -> dict:
    quotes = {}
    for expiry in expiries:
        for i in range(-span, span + 1):
            strike = round(spot / step) * step + i * step
            for kind in OptionKind:
                mid = option_mid(spot, strike, kind, (expiry - session).days, vol)
                if mid < 1.0:
                    continue
                half = max(0.05, mid * spread)
                quotes[ContractKey(expiry, strike, kind)] = SlotQuote(
                    round(mid - half, 2), round(mid + half, 2), 1000, 1000, round(mid, 2), True
                )
    return quotes


def scene(
    code=RoadCode.BANKNIFTY_MONTHLY,
    spot=SPOT,
    step=100.0,
    lot=30,
    days=(30, 60),
    session=SESSION,
    span=60,
    vol=VOL,
    spread=0.002,
):
    expiries = tuple(session + timedelta(days=d) for d in days)
    road_day = RoadDay(ROADS_BY_CODE[code], session, expiries, DatedLot(lot, "fixture"), step, OPEN)
    at = SLOT_AT.replace(year=session.year, month=session.month, day=session.day)
    snapshot = SlotSnapshot(code, session, f"fixture_{session:%Y%m%d}", "ab" * 32, at, at + timedelta(minutes=2), spot,
                            expiries, chain(spot, step, session, expiries, span, vol, spread))  # fmt: skip
    return road_day, snapshot


def history(spots, session: date = SESSION) -> tuple[SpotPoint, ...]:
    """`spots` oldest first, one per trading day ending the weekday before `session`."""
    days, day = [], session
    while len(days) < len(spots):
        day -= timedelta(days=1)
        if day.weekday() < 5:
            days.append(day)
    return tuple(SpotPoint(d, s) for d, s in zip(reversed(days), spots, strict=True))


def flat_history(length: int = 20, level: float = SPOT):
    return history([level] * length)


def cards():
    return load_cards(ROOT / CARDS_FOLDER)


def drivers() -> dict:
    return {d.card.code: d for d in build_drivers(cards(), BUILDER, CALENDAR)}


def position_from(decision, driver, session: date = SESSION, position_id: str = "p1") -> OpenPosition:
    proposal = decision.proposal
    return OpenPosition(position_id, driver.card.driver_id, decision.road, proposal.structure, proposal.legs,
                        proposal.lot, session, proposal.net_premium, proposal.max_loss)  # fmt: skip
