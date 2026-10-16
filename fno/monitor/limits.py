"""The alert limits (story LM1, design 6.5): a condition with the same key alerts at most once an hour (`hourly`) or
once a session (`once`); after the set number of DANGER alerts in a session, further DANGERs fold into one summary at
most every set minutes. Times are mark times, so a replay of the same marks gives the same decisions.

The history is the session's alert records (what was sent before this mark); this module keeps no state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .model import DANGER, DESK, HOURLY, ONCE, Condition
from .settings import MonitorSettings

SUMMARY_KEY = "danger_summary"
HOUR = timedelta(hours=1)


@dataclass(frozen=True)
class SentAlert:
    key: str
    severity: str
    mark: datetime  # the mark the alert was sent for


@dataclass(frozen=True)
class AlertDecision:
    send: tuple[Condition, ...] = ()
    summary: Condition | None = None
    held: tuple[Condition, ...] = field(default_factory=tuple)  # true on this mark, inside a limit: recorded, not sent


class AlertLimits:
    def __init__(self, settings: MonitorSettings):
        self.settings = settings

    def decide(self, conditions: list[Condition], history: list[SentAlert], mark: datetime) -> AlertDecision:
        due, held = [], []
        for condition in conditions:
            (due if self._due(condition, history, mark) else held).append(condition)
        dangers_sent = sum(1 for a in history if a.severity == DANGER and a.key != SUMMARY_KEY)
        room = max(self.settings.danger_summary_after - dangers_sent, 0)
        send, folded = [], []
        for condition in due:
            if condition.severity != DANGER:
                send.append(condition)
            elif room:
                send.append(condition)
                room -= 1
            else:
                folded.append(condition)
        summary = self._summary(folded, history, mark)
        held += [] if summary else folded
        return AlertDecision(tuple(send), summary, tuple(held))

    def _due(self, condition: Condition, history: list[SentAlert], mark: datetime) -> bool:
        before = [a.mark for a in history if a.key == condition.key]
        if not before:
            return True
        if condition.repeat == ONCE:
            return False
        return condition.repeat == HOURLY and mark - max(before) >= HOUR

    def _summary(self, folded: list[Condition], history: list[SentAlert], mark: datetime) -> Condition | None:
        if not folded:
            return None
        last = [a.mark for a in history if a.key == SUMMARY_KEY]
        if last and mark - max(last) < timedelta(minutes=self.settings.summary_every_minutes):
            return None
        counts: dict[str, int] = {}
        for condition in folded:
            counts[condition.check] = counts.get(condition.check, 0) + 1
        listed = ", ".join(f"{check} {n}" for check, n in sorted(counts.items()))
        facts = (f"{len(folded)} more DANGER conditions on this mark ({listed}); more than "
                 f"{self.settings.danger_summary_after} DANGER alerts this session, so one summary at most every "
                 f"{self.settings.summary_every_minutes} minutes")  # fmt: skip
        return Condition(SUMMARY_KEY, DANGER, DESK, SUMMARY_KEY, HOURLY, facts)
