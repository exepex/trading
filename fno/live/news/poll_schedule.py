"""Decides which source to ask next. One request at a time, spaced out, each source at its own pace.

- Sources start staggered across their interval, so they never all fire together.
- A source is never asked faster than its configured interval or its own cache time.
- Outside market hours every interval is stretched (news still arrives, nothing is being traded).
- A source that fails waits longer each time (doubling, up to 30 minutes); one with a daily allowance stops for the
  day when it is used up.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from ...models import IST
from .source import NewsSource

MARKET_OPENS = time(9, 0)  # a little before the 09:15 open: pre-open news matters
MARKET_CLOSES = time(15, 30)
MAX_BACKOFF_SECONDS = 30 * 60


def in_market_hours(now: datetime) -> bool:
    local = now.astimezone(IST)
    return local.weekday() < 5 and MARKET_OPENS <= local.time() <= MARKET_CLOSES


@dataclass
class SourcePlan:
    source: NewsSource
    every_seconds: float
    daily_limit: int | None = None
    next_due: datetime | None = None
    failures: int = 0
    used_today: int = 0
    usage_day: date | None = None
    polls: int = field(default=0)

    @property
    def name(self) -> str:
        return self.source.name


class PollSchedule:
    def __init__(self, plans: list[SourcePlan], min_gap_seconds: float = 5.0, off_hours_factor: float = 5.0):
        self.plans = plans
        self.min_gap = timedelta(seconds=min_gap_seconds)
        self.off_hours_factor = off_hours_factor
        self._last_request: datetime | None = None

    def start(self, now: datetime) -> None:
        """Spread first requests out: source i starts i gaps after the first."""
        for i, plan in enumerate(self.plans):
            plan.next_due = now + self.min_gap * i

    def next_request(self, now: datetime) -> tuple[SourcePlan | None, datetime]:
        """The source to ask next and when (never sooner than the gap since the last request)."""
        ready = [p for p in self.plans if p.next_due is not None and self._has_allowance(p, now)]
        if not ready:
            return None, now + timedelta(minutes=5)
        plan = min(ready, key=lambda p: p.next_due)
        earliest = self._last_request + self.min_gap if self._last_request else now
        return plan, max(plan.next_due, earliest, now)

    def record(self, plan: SourcePlan, now: datetime, ok: bool, pause_seconds: float | None = None) -> None:
        self._last_request = now
        plan.polls += 1
        self._count_usage(plan, now)
        interval = self.interval(plan, now)
        if ok:
            plan.failures = 0
        else:
            plan.failures += 1
            interval = min(interval * 2**plan.failures, MAX_BACKOFF_SECONDS)
        if pause_seconds:
            interval = max(interval, pause_seconds)
        plan.next_due = now + timedelta(seconds=interval)

    def interval(self, plan: SourcePlan, now: datetime) -> float:
        planned = plan.every_seconds if in_market_hours(now) else plan.every_seconds * self.off_hours_factor
        return max(planned, plan.source.min_interval_seconds)  # the source's own cache time is a floor only

    def _count_usage(self, plan: SourcePlan, now: datetime) -> None:
        today = now.astimezone(IST).date()
        if plan.usage_day != today:
            plan.usage_day, plan.used_today = today, 0
        plan.used_today += 1

    @staticmethod
    def _has_allowance(plan: SourcePlan, now: datetime) -> bool:
        if plan.daily_limit is None or plan.usage_day != now.astimezone(IST).date():
            return True
        return plan.used_today < plan.daily_limit
