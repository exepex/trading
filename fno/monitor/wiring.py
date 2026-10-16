"""The position monitor's composition root (story LM1). Round 1 builds the pure monitor and its limits; A16's
observer port, the position and mark adapters and the alert path are wired here in the next round."""

from __future__ import annotations

from ..desk.timetable import timetable_from_config
from ..research_data.calendar import load_session_calendar
from ..storage.wiring import CALENDAR_FILE
from .checks import BigMove, ExitRuleReached, ExpiryNear, LossUsed, QuotesStale, ShortStrikeNear
from .limits import AlertLimits
from .monitor import PositionMonitor
from .settings import MonitorSettings


def monitor_settings(cfg: dict) -> MonitorSettings:
    return MonitorSettings.from_config(cfg["monitor"], timetable_from_config(cfg).execution_snapshot)


def build_position_monitor(cfg: dict) -> PositionMonitor:
    settings = monitor_settings(cfg)
    checks = [LossUsed(settings), ShortStrikeNear(settings), ExitRuleReached(settings), BigMove(settings),
              ExpiryNear(settings, load_session_calendar(CALENDAR_FILE))]  # fmt: skip
    return PositionMonitor(settings, checks, QuotesStale(settings))


def build_alert_limits(cfg: dict) -> AlertLimits:
    return AlertLimits(monitor_settings(cfg))
