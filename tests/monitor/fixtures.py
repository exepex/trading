"""Plain fixtures for the position monitor's tests (story LM1): a mark, a put credit spread, the settings."""

from __future__ import annotations

from datetime import date, datetime, time

from fno.models import IST
from fno.monitor.model import MonitorMark, WatchedLeg, WatchedPosition
from fno.monitor.settings import MonitorSettings
from fno.research_engine.structures import BOUGHT, SOLD, Leg

DAY = date(2026, 10, 16)
EXPIRY = date(2026, 10, 27)
SECTION = {
    "version": "test-1", "loss_used_warning": 0.5, "loss_used_danger": 0.8, "short_strike_near_pct": 0.5,
    "big_move_pct": 1.5, "big_move_step_pct": 0.5, "stale_after_minutes": 30, "check_incomplete_marks": True,
    "expiry_warn_sessions": 1, "danger_summary_after": 10, "summary_every_minutes": 30,
}  # fmt: skip


def settings(**changes) -> MonitorSettings:
    return MonitorSettings.from_config({**SECTION, **changes}, time(15, 15))


def at(hhmm: str, day: date = DAY) -> datetime:
    return datetime.combine(day, time.fromisoformat(hhmm), IST)


THIS_MARK = object()


def mark(hhmm="10:30", level=25000.0, previous=25000.0, status="good", last_good=THIS_MARK, day=DAY) -> MonitorMark:
    when = at(hhmm, day)
    return MonitorMark(day, when, status, level, previous, when if last_good is THIS_MARK else last_good)


def spread(trade="T1", loss=1000.0, max_loss=10000.0, short=24500.0, expiry=EXPIRY, **more) -> WatchedPosition:
    legs = (WatchedLeg(Leg(short, "PE", SOLD), expiry), WatchedLeg(Leg(short - 200, "PE", BOUGHT), expiry))
    return WatchedPosition(trade, "book1", legs, max_loss, loss, **more)
