"""Before a confirmatory look, every scheduled AI slot-day must be settled (ChatGPT review 127, response 213;
agreed with G11). G11 writes one v4 record row for each registered hybrid or ai_team slot, question and session day
once the day settles, whatever the outcome (ok, or a definitive miss such as not_fired or no_submission). A session
from the slot's counted start to the look's date with no row (a sealed answer never collected, a collect that died, an
audit still open) is unsettled, and the look refuses rather than record a provisional miss. The rules slot's gaps stay
ordinary misses."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from ...constants import V4_SLOT_AI, V4_SLOT_HYBRID
from .audits import LookBlocked
from .inputs import V4ForecastSource
from .records import SlotRegistry

AI_SLOTS = (V4_SLOT_HYBRID, V4_SLOT_AI)
UNSETTLED = ("a look on {look} needs every AI slot-day settled: {count} without a record row, the earliest {day} "
             "({question}, {slot})")  # fmt: skip


@dataclass(frozen=True)
class SlotDay:
    day: date
    question: str
    slot: str


class AiSlotDays:
    """`sessions(first, last)`: the v4 scored sessions in [first, last] that are not system_late."""

    def __init__(self, forecasts: V4ForecastSource, registry: SlotRegistry,
                 sessions: Callable[[date, date], list[date]]):  # fmt: skip
        self.forecasts, self.registry, self.sessions = forecasts, registry, sessions

    def unsettled(self, freeze_day: date, look_day: date) -> list[SlotDay]:
        missing = []
        for (question, slot), registration in self.registry.registered().items():
            if slot not in AI_SLOTS:
                continue
            held = self.forecasts.values(question, registration.forecaster)  # a row of any status settles the day
            start = max(registration.effective_start, freeze_day + timedelta(days=1))
            missing += [SlotDay(d, question, slot) for d in self.sessions(start, look_day) if d not in held]
        return sorted(missing, key=lambda s: (s.day, s.question, s.slot))


def require_reconciled(unsettled: list[SlotDay], look_day: date) -> None:
    if unsettled:
        first = unsettled[0]
        raise LookBlocked(UNSETTLED.format(look=look_day, count=len(unsettled), day=first.day,
                                           question=first.question, slot=first.slot))  # fmt: skip
