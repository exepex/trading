"""The monitor's alert texts (story LM1, design 6.5). Every alert starts "F&O monitor:", never E8's "F&O paper desk
<book>: EXIT", so the two never look alike on a phone. The first line says what to do, or "information, no action". The
last line says what the paper record assumes if the owner acts 60 minutes later: in `alert_only` it changes only at a
daily run's execution snapshot. No text names a contract's price, and none uses the words exit or close (E8's)."""

from __future__ import annotations

from ..models import IST
from .model import Condition, MonitorMark
from .settings import MonitorSettings

PREFIX = "F&O monitor:"
INFORMATION = "information, no action"
ACTIONS = {
    "loss_used": "review {trade} now",
    "cannot_mark": "look at {trade} in Groww yourself; the monitor cannot measure it",
    "short_strike_near": "review {trade} now",
    "expiry_near": "check {trade}'s plan for its expiry",
    "big_move": "review every open position",
    "quotes_stale": "check A16's quote recorder (story A16); positions are not being watched",
    "danger_summary": "review every open position",
    "expiry_uncounted": "check {trade}'s expiry date yourself; NSE's calendar needs next year's holiday rows",
    "check_failed": "tell the LM1 builder; this check is not watching until fixed",
}
MARK_LINE = "Mark {mark} IST; thresholds {version}."
LATER = ("If you act 60 minutes later, the paper record is the same: it changes only at {when} (alert_only; "
         "nothing in this monitor trades).")  # fmt: skip
TODAY = "today's execution snapshot ({at:%H:%M})"
NEXT_SESSION = "the next session's execution snapshot ({at:%H:%M})"


def alert_text(condition: Condition, mark: MonitorMark, settings: MonitorSettings) -> str:
    return "\n".join((
        f"{PREFIX} {condition.severity}, {first_line(condition)}",
        condition.facts,
        MARK_LINE.format(mark=f"{mark.mark.astimezone(IST):%H:%M}", version=settings.version),
        later_line(mark, settings),
    ))  # fmt: skip


def first_line(condition: Condition) -> str:
    if condition.information_only:
        return INFORMATION
    return "action: " + ACTIONS[condition.check].format(trade=condition.trade_id)


def later_line(mark: MonitorMark, settings: MonitorSettings) -> str:
    snapshot = settings.execution_snapshot
    before = mark.mark.astimezone(IST).time() < snapshot
    return LATER.format(when=(TODAY if before else NEXT_SESSION).format(at=snapshot))
