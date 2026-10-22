"""Small valid instructor fixtures (story MS-INS): a trade or ticket sealed on the fake dashcam and held over several
sessions. Fixed values only: no live strike, price or capture."""

from dataclasses import replace
from datetime import date, datetime

from fno.constants import SIDE_BUY, SIDE_SELL
from fno.school.constants import SLOT_1500, ExitReason, NoTradeReason, Outcome, RecordKind, RoadCode
from fno.school.contracts.accounts import FilledLeg, FillResult
from fno.school.contracts.decisions import Decision
from fno.school.contracts.records import DecisionRecord, ExitRecord, OutcomeRecord
from fno.school.fakes import FakeDashcam
from fno.school.instructor.contracts import Attribution, Cause, Classification, Modifier
from tests.school.contracts.builders import IST, key, put_spread, snapshot

ROAD = RoadCode.BANKNIFTY_MONTHLY
DRIVER, OTHER = "CS1@1", "REF@1"
SESSIONS = (date(2026, 11, 2), date(2026, 11, 3), date(2026, 11, 4))
RULES = "ef" * 32


def at(day: date, minute: int = 4) -> datetime:
    return datetime(day.year, day.month, day.day, 15, minute, tzinfo=IST)


def snap(day: date, sha: str | None = None):
    return replace(
        snapshot(ROAD), session=day, snapshot_id=f"fixture_{day:%Y%m%d}", sha256=sha or f"{day.day:02d}" * 32
    )


def decision_record(day: date, driver: str = DRIVER, outcome: Outcome = Outcome.TRADE, road_open: bool = True):
    shot = snap(day)
    reason = "" if outcome == Outcome.TRADE else NoTradeReason.POSITION_OPEN
    proposal = put_spread() if outcome in (Outcome.TRADE, Outcome.TICKET) else None
    if outcome == Outcome.TICKET:
        reason = "trade_limit"
    decision = Decision(driver, ROAD, day, outcome, reason, proposal)
    return DecisionRecord(day, SLOT_1500, ROAD, "aa" * 32, shot.snapshot_id, shot.sha256, None, decision)


def closed_record(day: date, driver: str = DRIVER) -> DecisionRecord:
    decision = Decision(driver, ROAD, day, Outcome.ROAD_CLOSED, "capture_missing")
    return DecisionRecord(day, SLOT_1500, ROAD, "aa" * 32, "", "", "capture_missing", decision)


def fill(day: date, side: str, price: float, rests_on: str) -> FillResult:
    return FillResult(
        (
            FilledLeg(key(1000.0), side, 30, price, 20.0),
            FilledLeg(key(900.0), SIDE_BUY if side == SIDE_SELL else SIDE_SELL, 30, 4.0, 20.0),
        ),
        filled_at=at(day),
        rests_on=rests_on,
    )


def outcome(
    entry_sha: str,
    entry_day: date = SESSIONS[0],
    exit_day: date = SESSIONS[-1],
    is_ticket: bool = False,
    exit_reason: ExitReason = ExitReason.PROFIT_TARGET,
    exit_price: float = 12.0,
    corrects: str = "",
    exit_rests_on: str = "00" * 32,
) -> OutcomeRecord:
    """The net is its fills' cash, as every real outcome's is (judge 503)."""
    entry = fill(entry_day, SIDE_SELL, 10.0, entry_sha)
    leaving = fill(exit_day, SIDE_BUY, exit_price, exit_rests_on)
    net = entry.cash + leaving.cash
    return OutcomeRecord(
        "p1",
        DRIVER,
        ROAD,
        entry_sha,
        entry,
        leaving,
        exit_reason,
        -15.0,
        80.0,
        net,
        net / 2500.0,
        30.0,
        is_ticket,
        corrects,
    )


def refilled(record: OutcomeRecord, exit_price: float, **changes) -> OutcomeRecord:
    """The same outcome with its exit at another price and the net that follows from it: a valid correction."""
    legs = (replace(record.exit.legs[0], price=exit_price),) + record.exit.legs[1:]
    leaving = replace(record.exit, legs=legs)
    net = record.entry.cash + leaving.cash
    return replace(record, exit=leaving, net=net, return_on_risk=net / 2500.0, **changes)


def held_trade(dashcam: FakeDashcam, ticket: bool = False, closed_middle: bool = False) -> OutcomeRecord:
    """A trade (or ticket) entered on the first session, held over the second, closed on the third."""
    first = Outcome.TICKET if ticket else Outcome.TRADE
    seal = dashcam.seal(
        SESSIONS[0],
        SLOT_1500,
        RecordKind.DECISIONS,
        (decision_record(SESSIONS[0], outcome=first), decision_record(SESSIONS[0], OTHER)),
    )
    middle = (closed_record(SESSIONS[1]),) if closed_middle else (decision_record(SESSIONS[1], OTHER),)
    dashcam.seal(SESSIONS[1], SLOT_1500, RecordKind.DECISIONS, middle)
    dashcam.seal(
        SESSIONS[2],
        SLOT_1500,
        RecordKind.DECISIONS,
        (
            decision_record(SESSIONS[2], OTHER),
            ExitRecord(SESSIONS[2], SLOT_1500, "p1", DRIVER, ROAD, ExitReason.PROFIT_TARGET, "x"),
        ),
    )
    record = outcome(seal.sha256, is_ticket=ticket)
    dashcam.seal(SESSIONS[2], SLOT_1500, RecordKind.OUTCOMES, (record,))
    return record


def attribution(**changes) -> Attribution:
    values = dict(
        position_id="p1",
        driver_id=DRIVER,
        road=ROAD,
        closed_on=SESSIONS[-1],
        is_ticket=False,
        delta=-120.0,
        gamma=-10.0,
        vega=40.0,
        theta=75.0,
        residual=0.0,
        charges=60.0,
        spread=20.0,
        net=-95.0,
        steps=2,
        steps_merged=0,
        iv_unsolved=0,
        poor_fit=False,
        rules_sha256=RULES,
    )
    return Attribution(**{**values, **changes})


def classification(**changes) -> Classification:
    values = dict(
        position_id="p1",
        driver_id=DRIVER,
        road=ROAD,
        closed_on=SESSIONS[-1],
        is_ticket=False,
        net=-95.0,
        primary=Cause.WRONG_DIRECTION,
        secondary=(Cause.COSTS_ATE_EDGE,),
        not_testable=(),
        modifier=Modifier.NONE,
        rules_sha256=RULES,
    )
    return Classification(**{**values, **changes})
