"""A clock that moves only when the run sleeps or a read takes time, and parts that answer from a script."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, time, timedelta

from fno.preopen.answers import Reading
from fno.preopen.parts import Answer, PartFailed, PreopenPart


class FakeClock:
    def __init__(self, start: datetime):
        self.at, self.slept = start, []

    def now(self) -> datetime:
        return self.at

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.at += timedelta(seconds=seconds)


class ScriptedPart(PreopenPart):
    """Answers `script(n, now)` on its n-th read (from 1): a Reading, or an exception to raise."""

    def __init__(self, name: str, window: tuple[time, time], clock: FakeClock,
                 script: Callable[[int, datetime], Reading | Exception], takes: float = 0.0):  # fmt: skip
        self.name, self.window, self.clock, self.script, self.takes = name, window, clock, script, takes
        self.read_at: list[datetime] = []

    def answer(self, day: date) -> Answer:
        self.read_at.append(self.clock.now())
        self.clock.at += timedelta(seconds=self.takes)
        outcome = self.script(len(self.read_at), self.clock.now())
        if isinstance(outcome, Exception):
            raise outcome
        return Answer(f"raw {self.name} {len(self.read_at)}".encode(), outcome, self.clock.now())


def complete(values: dict | None = None) -> Callable:
    return lambda n, now: Reading(True, now, values or {})


def never(detail: str = "not yet") -> Callable:
    return lambda n, now: Reading(False, None, {}, detail)


def failing(n, now):
    return PartFailed("NSE: HTTP 503")
