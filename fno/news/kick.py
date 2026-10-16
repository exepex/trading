"""The only starter besides a run's own successor (story A19, scope 7; judge 352 SF2): on a cron or when a
news-capture run completes, start one only when the window is open (or the bridge is on) and no news-capture run is
queued or in progress, so a cron never queues behind a live poller and is never cancelled. After a completed run it
acts only on a failure: a run of at least 10 minutes is restarted; a shorter one (a failure at start) is not, so a
broken start never loops, and that is recorded once. A run GitHub cancelled before any step ran was replaced, not
lost: nothing to do."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .window import PollingWindow

SHORTEST_RESTARTED = timedelta(minutes=10)
SUCCESS, CANCELLED = "success", "cancelled"
DISPATCH, NOTHING, STOPPED = "dispatch", "nothing", "restart_stopped"


@dataclass(frozen=True)
class CompletedRun:
    conclusion: str
    started_at: datetime
    ended_at: datetime
    steps_ran: bool
    url: str

    @property
    def lasted(self) -> timedelta:
        return self.ended_at - self.started_at


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str


def decide(now: datetime, window: PollingWindow, bridge: bool, active_runs: int,
           completed: CompletedRun | None = None) -> Decision:  # fmt: skip
    """`completed`: the run whose completion started the kick (None for a cron)."""
    if completed is not None:
        if completed.conclusion == SUCCESS:
            return Decision(NOTHING, "the run succeeded and dispatched its own successor")
        if completed.conclusion == CANCELLED and not completed.steps_ran:
            return Decision(NOTHING, "the run was replaced in the queue before any step ran")
        if completed.lasted < SHORTEST_RESTARTED:
            minutes = completed.lasted.total_seconds() / 60
            return Decision(STOPPED, f"the run ended {completed.conclusion} after {minutes:.1f} min: not restarted")
    if not (bridge or window.is_open(now)):
        return Decision(NOTHING, "the polling window is closed")
    if active_runs:
        return Decision(NOTHING, f"{active_runs} news-capture run(s) already queued or running")
    return Decision(DISPATCH, "restart after a failed run" if completed else "no poller alive")


def wants_successor(lasted: timedelta, now: datetime, window: PollingWindow, bridge: bool) -> bool:
    """A run's own successor: only after at least 10 minutes (a failure at start never loops) and while the window
    is open or the bridge keeps the chain alive overnight."""
    return lasted >= SHORTEST_RESTARTED and (bridge or window.is_open(now))
