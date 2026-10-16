"""Failure episodes (story A19, scope 9): the first failure of a kind on a step writes one row in O10's capture-error
log and sends one alert; repeats add nothing; the first success after it writes one `<kind>_recovered` row and one
alert. The log itself is the state: a run starts from the episodes left open there, so a restart never re-alerts.
Messages carry names and counts only (a feed id, an HTTP status), never an item's headline or link."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime

from ..alerts.sender import SENT, AlertSender
from ..models import IST
from .names import COVERAGE_GAP, JOB, RECOVERED_SUFFIX, RESTART_STOPPED

OPENED = "Omenix F&O news: {step} {kind} since {since} IST ({detail})"
CLOSED = "Omenix F&O news: {step} {kind} recovered after {minutes} min, {count} failed poll(s)"
CLOSED_CARRIED = "Omenix F&O news: {step} {kind} recovered (open since {day}, before this run)"
ALERT_FAILED = "; {outcome}"
EVENT_KINDS = (COVERAGE_GAP, RESTART_STOPPED)  # one-off rows: nothing stays open


@dataclass(frozen=True)
class LogRow:
    day: date
    job: str
    step: str
    kind: str


class EpisodeLog(ABC):
    """O10's committed capture-error log, seen through what A19 needs."""

    @abstractmethod
    def rows(self) -> list[LogRow]: ...

    @abstractmethod
    def append(self, day: date, step: str, kind: str, message: str) -> None: ...


@dataclass
class Episode:
    since: datetime | None  # None: opened by an earlier run (the log keeps only its date)
    day: date
    count: int = 1


class Episodes:
    def __init__(self, log: EpisodeLog, alerts: AlertSender, clock: Callable[[], datetime], out=print):
        self.log, self.alerts, self.clock, self.out = log, alerts, clock, out
        self.open: dict[tuple[str, str], Episode] = _open_in(log.rows())

    def fail(self, step: str, kind: str, detail: str) -> None:
        episode = self.open.get((step, kind))
        if episode is not None:
            episode.count += 1
            return
        now = self.clock()
        self.open[(step, kind)] = Episode(now, now.astimezone(IST).date())
        self._record(
            step, kind, OPENED.format(step=step, kind=kind, since=f"{now.astimezone(IST):%H:%M}", detail=detail)
        )

    def ok(self, step: str, kinds: tuple[str, ...] | None = None) -> None:
        """The step worked: closes its open episodes (all of them, or only `kinds`)."""
        for key in [k for k in self.open if k[0] == step and (kinds is None or k[1] in kinds)]:
            episode = self.open.pop(key)
            self._record(step, key[1] + RECOVERED_SUFFIX, self._closing(key, episode))

    def event(self, step: str, kind: str, text: str) -> None:
        """A one-off failure with no recovery to wait for (a coverage gap, a stopped restart): one row, one alert."""
        self._record(step, kind, text)

    def is_open(self, step: str, kind: str) -> bool:
        return (step, kind) in self.open

    def _closing(self, key: tuple[str, str], episode: Episode) -> str:
        step, kind = key
        if episode.since is None:
            return CLOSED_CARRIED.format(step=step, kind=kind, day=episode.day.isoformat())
        minutes = round((self.clock() - episode.since).total_seconds() / 60)
        return CLOSED.format(step=step, kind=kind, minutes=minutes, count=episode.count)

    def _record(self, step: str, kind: str, text: str) -> None:
        outcome = self.alerts.send(text)
        self.out(f"{text} -> {outcome}")
        message = text if outcome == SENT else text + ALERT_FAILED.format(outcome=outcome)
        self.log.append(self.clock().astimezone(IST).date(), step, kind, message)


def _open_in(rows: list[LogRow]) -> dict[tuple[str, str], Episode]:
    open_: dict[tuple[str, str], Episode] = {}
    for row in rows:
        if row.job != JOB or row.kind in EVENT_KINDS:
            continue
        if row.kind.endswith(RECOVERED_SUFFIX):
            open_.pop((row.step, row.kind.removesuffix(RECOVERED_SUFFIX)), None)
        else:
            open_[(row.step, row.kind)] = Episode(None, row.day)
    return open_
