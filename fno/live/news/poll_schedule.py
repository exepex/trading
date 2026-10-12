"""Decides which source to ask next. One request at a time, spaced out, each source at its own pace.

- Sources start staggered across their interval, so they never all fire together.
- A source is never asked faster than its configured interval or its own cache time.
- Only while the Indian market is open (trading days, 08:45-15:45 IST by default): nothing is asked outside it.
- A source that fails waits longer each time (doubling, up to 30 minutes); one with a daily allowance stops for the
  day when it is used up.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path

from ...models import IST
from .source import NewsSource

log = logging.getLogger(__name__)

DEFAULT_ACTIVE_FROM = time(8, 45)  # half an hour before the 09:15 open: pre-open news matters
DEFAULT_ACTIVE_UNTIL = time(15, 45)  # a little after the 15:30 close
MAX_BACKOFF_SECONDS = 30 * 60
LOOKAHEAD_DAYS = 10  # far enough to cross a long weekend plus holidays


def weekday(day: date) -> bool:
    return day.weekday() < 5


@dataclass
class ActiveWindow:
    """When the watcher works: trading days only, between two IST times."""

    starts: time = DEFAULT_ACTIVE_FROM
    ends: time = DEFAULT_ACTIVE_UNTIL
    is_trading_day: Callable[[date], bool] = weekday

    def contains(self, now: datetime) -> bool:
        local = now.astimezone(IST)
        return self.is_trading_day(local.date()) and self.starts <= local.time() <= self.ends

    def next_start(self, now: datetime) -> datetime:
        local = now.astimezone(IST)
        for offset in range(LOOKAHEAD_DAYS):
            day = local.date() + timedelta(days=offset)
            start = datetime.combine(day, self.starts, IST)
            if self.is_trading_day(day) and (start > local or self.contains(local)):
                return max(start, local)
        return local + timedelta(days=1)


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
    def __init__(
        self,
        plans: list[SourcePlan],
        min_gap_seconds: float = 5.0,
        window: ActiveWindow | None = None,
        usage_file: Path | None = None,
    ):
        """usage_file keeps each source's requests today across restarts (paid and capped allowances)."""
        self.plans = plans
        self.min_gap = timedelta(seconds=min_gap_seconds)
        self.window = window or ActiveWindow()
        self.usage_file = usage_file
        self._last_request: datetime | None = None
        self._load_usage()

    def start(self, now: datetime) -> None:
        """Spread first requests out: source i starts i gaps after the first."""
        for i, plan in enumerate(self.plans):
            plan.next_due = now + self.min_gap * i

    def next_request(self, now: datetime) -> tuple[SourcePlan | None, datetime]:
        """The source to ask next and when (never sooner than the gap since the last request). Outside the window:
        no source, and the time the window opens again."""
        if not self.window.contains(now):
            opens = self.window.next_start(now)
            for plan in self.plans:  # stagger again from the opening, as on a fresh start
                plan.next_due = None
            return None, opens
        if all(p.next_due is None for p in self.plans):
            self.start(now)
        ready = [p for p in self.plans if p.next_due is not None and self._has_allowance(p, now)]
        if not ready:
            return None, now + timedelta(minutes=5)
        plan = min(ready, key=lambda p: p.next_due)
        earliest = self._last_request + self.min_gap if self._last_request else now
        return plan, max(plan.next_due, earliest, now)

    def prioritise(self, source_names: set[str], now: datetime) -> None:
        """Ask these sources next (a sudden price move suggests news): still one at a time, still within limits."""
        for plan in self.plans:
            if plan.name in source_names and plan.next_due is not None and plan.next_due > now:
                plan.next_due = now

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
        return max(plan.every_seconds, plan.source.min_interval_seconds)  # the source's own cache time is a floor

    def _count_usage(self, plan: SourcePlan, now: datetime) -> None:
        today = now.astimezone(IST).date()
        if plan.usage_day != today:
            plan.usage_day, plan.used_today = today, 0
        plan.used_today += 1
        if plan.daily_limit is not None:
            self._save_usage()

    def _load_usage(self) -> None:
        if self.usage_file is None or not self.usage_file.exists():
            return
        try:
            saved = json.loads(self.usage_file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            log.warning("news usage file unreadable, counting from zero: %s", exc)
            return
        for plan in self.plans:
            day, used = saved.get(plan.name, (None, 0))
            if day:
                plan.usage_day, plan.used_today = date.fromisoformat(day), int(used)

    def _save_usage(self) -> None:
        if self.usage_file is None:
            return
        usage = {p.name: (p.usage_day.isoformat(), p.used_today) for p in self.plans if p.usage_day}
        try:
            self.usage_file.parent.mkdir(parents=True, exist_ok=True)
            self.usage_file.write_text(json.dumps(usage), encoding="utf-8")
        except OSError as exc:
            log.warning("could not save news usage: %s", exc)

    @staticmethod
    def _has_allowance(plan: SourcePlan, now: datetime) -> bool:
        if plan.daily_limit is None or plan.usage_day != now.astimezone(IST).date():
            return True
        return plan.used_today < plan.daily_limit
