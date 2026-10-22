"""The A16h probe of Groww's streaming feed (story A16h): one plan per run, inside its own window, counts and times
only (no tick value is ever kept or printed). Every plan unsubscribes everything and stops at once, with one named
line, when a call raises (a 429 named as such) or its hard end time is reached."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from ..models import IST
from .feed_ticks import TickCounter
from .feed_universe import INDEX, FeedInstrument

RAMP_STEPS = (500, 1000, 1500, 2000, 3000)
SAMPLE_SECONDS, STEP_SECONDS = 5, 45
RATE_LIMITED, FAILED, ENDED = "rate limited (429)", "failed", "hard end time reached"
LTP, INDEX_VALUE = "ltp", "index_value"  # the feed types whose answers carry an exchange time


@dataclass(frozen=True)
class Plan:
    name: str
    start: time
    latest_start: time
    end: time
    cap: int  # the most instruments the plan may hold
    depth: bool = False  # also subscribe market depth (coverage only)


PLANS = {plan.name: plan for plan in (
    Plan("coverage", time(10, 20), time(10, 25), time(10, 40), 1000, depth=True),
    Plan("ramp", time(15, 45), time(16, 0), time(16, 15), RAMP_STEPS[-1]),  # after the close (A16's 15:30 mark is in)
    Plan("ramp-day", time(10, 50), time(10, 51), time(10, 58), RAMP_STEPS[-1]),  # between A16's 10:45 and 11:00 marks
    Plan("alongside", time(14, 30), time(14, 50), time(15, 20), 1000),  # signed in and subscribed before 14:50
)}  # fmt: skip


class ProbeRefused(RuntimeError):
    """The plan may not start now, or would hold more subscriptions than its cap."""


@dataclass
class Outcome:
    plan: str
    requested: int = 0
    accepted: int = 0
    stop: str = ""
    reached: int = 0  # ramp: the subscriptions held when it stopped
    lines: list[str] = field(default_factory=list)


class FeedProbe:
    def __init__(self, feed, clock: Callable[[], datetime], sleep: Callable[[float], None]):
        self.feed, self.clock, self.sleep = feed, clock, sleep
        self.ticks = TickCounter(clock)
        self.held: list[FeedInstrument] = []
        self.depth_held: list[FeedInstrument] = []

    def run(
        self, plan: Plan, instruments: Sequence[FeedInstrument], day: date, minutes: float | None = None
    ) -> Outcome:
        self._may_start(plan, day, 0 if _is_ramp(plan) else len(instruments))
        outcome = Outcome(plan.name, requested=len(instruments))
        end = datetime.combine(day, plan.end, IST)
        if minutes is not None:
            end = min(end, self.clock() + timedelta(minutes=minutes))
        try:
            if _is_ramp(plan):
                self._ramp(instruments, end, outcome)
            else:
                self._subscribe(instruments, outcome, plan.depth)
                self._watch(end)
        except Exception as error:  # every failure stops the run: the class name only (its text could hold a secret)
            outcome.stop = f"{RATE_LIMITED if _rate_limited(error) else FAILED}: {type(error).__name__}"
        finally:
            outcome.lines += self._unsubscribe_all()
        outcome.stop = outcome.stop or ENDED
        outcome.lines = self.ticks.report(self.ticks.classes) + outcome.lines
        return outcome

    def _may_start(self, plan: Plan, day: date, count: int) -> None:
        now = self.clock().astimezone(IST)
        first, last = (datetime.combine(day, t, IST) for t in (plan.start, plan.latest_start))
        if not first <= now <= last:
            raise ProbeRefused(f"{plan.name} may start only {plan.start:%H:%M}-{plan.latest_start:%H:%M} IST")
        if count > plan.cap:
            raise ProbeRefused(f"{plan.name} may hold at most {plan.cap} subscriptions, asked for {count}")

    def _subscribe(self, instruments: Sequence[FeedInstrument], outcome: Outcome, depth: bool = False) -> None:
        indices = [i for i in instruments if i.kind == INDEX]
        others = [i for i in instruments if i.kind != INDEX]
        self.held += list(instruments)  # before the call: a call that raises may already have subscribed some
        if depth:
            self.depth_held += others
        self.ticks.classes.update({i.token: i.feed_class() for i in instruments})
        if indices:
            outcome.accepted += _created(self.feed.subscribe_index_value([i.subscription() for i in indices],
                                                                         self.ticks.on_tick))  # fmt: skip
        if others:
            outcome.accepted += _created(
                self.feed.subscribe_ltp([i.subscription() for i in others], self.ticks.on_tick)
            )
        if others and depth:
            outcome.accepted += _created(self.feed.subscribe_market_depth([i.subscription() for i in others],
                                                                          self.ticks.on_tick))  # fmt: skip

    def _watch(self, end: datetime) -> None:
        while self.clock() < end:
            self._wait(SAMPLE_SECONDS, end)
            self.ticks.sample(self.feed.get_ltp(), LTP)
            self.ticks.sample(self.feed.get_index_value(), INDEX_VALUE)

    def _ramp(self, instruments: Sequence[FeedInstrument], end: datetime, outcome: Outcome) -> None:
        for step in RAMP_STEPS:
            if self.clock() >= end:
                return
            self._subscribe(instruments[len(self.held) : step], outcome)
            outcome.reached = len(self.held)
            outcome.lines.append(f"ramp: {outcome.reached} subscriptions held")
            self._wait(STEP_SECONDS, end)
            self.feed.get_ltp()  # a refused or dropped subscription set shows here as a raised error

    def _wait(self, seconds: float, end: datetime) -> None:
        """Never past the plan's hard end time."""
        left = (end - self.clock()).total_seconds()
        if left > 0:
            self.sleep(min(seconds, left))

    def _unsubscribe_all(self) -> list[str]:
        lines = []
        plan = (("unsubscribe_index_value", [i for i in self.held if i.kind == INDEX]),
                ("unsubscribe_ltp", [i for i in self.held if i.kind != INDEX]),
                ("unsubscribe_market_depth", self.depth_held))  # fmt: skip
        for call, instruments in plan:
            held = [i.subscription() for i in instruments]
            if not held:
                continue
            try:
                getattr(self.feed, call)(held)
            except Exception as error:
                lines.append(f"{call} failed: {type(error).__name__}")
        self.held, self.depth_held = [], []
        return lines


def _created(answer) -> int:
    """How many topics the feed says it newly subscribed (its answer nests exchange -> segment -> key -> bool)."""
    if isinstance(answer, bool):
        return int(answer)
    if isinstance(answer, dict):
        return sum(_created(value) for value in answer.values())
    return 0


def _is_ramp(plan: Plan) -> bool:
    return plan.name.startswith("ramp")


def _rate_limited(error: Exception) -> bool:
    return str(getattr(error, "code", "")) == "429" or "429" in type(error).__name__


def summary(outcome: Outcome) -> list[str]:
    head = f"feed probe {outcome.plan}: {outcome.accepted} of {outcome.requested} subscribed; stopped: {outcome.stop}"
    return [head, *outcome.lines]
