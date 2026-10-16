"""What the position monitor sees on one A16 mark, and what it finds (story LM1). Pure values: the adapters that build
them from A16's snapshot and the desk's records come in a later round, so every check is tested on plain fixtures.

A position carries its maximum loss fixed at entry and its loss if closed now at the mark's touch, already computed
(None when a leg is not on the mark: "cannot mark", never a guessed price)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from ..research_engine.structures import Leg

DANGER, WARNING = "DANGER", "WARNING"
POSITION, DESK = "position", "desk"  # a condition about one position, or about the market for the whole desk
HOURLY, ONCE = "hourly", "once"  # repeat at most once an hour while it lasts, or once per session per key


@dataclass(frozen=True)
class MonitorMark:
    session: date
    mark: datetime  # the mark's time (A16's slot), with its offset
    status: str  # A16's slot status
    index_level: float | None  # NIFTY on the mark; None when the mark has no good index reading
    previous_close: float | None  # NSE's close of the previous session
    last_good_at: datetime | None  # the latest mark the monitor could check, this one included when usable
    clock_skew_seconds: float | None = None  # A16's clock check, carried into the alert record


@dataclass(frozen=True)
class WatchedLeg:
    leg: Leg
    expiry: date


@dataclass(frozen=True)
class WatchedPosition:
    trade_id: str
    book: str
    legs: tuple[WatchedLeg, ...]
    max_loss_rs: float  # fixed at entry (C2/C5's model); positive
    loss_now_rs: float | None  # the loss if every leg closed at this mark's touch (negative: a gain); None: unmarked
    exit_rules_reached: tuple[str, ...] = ()  # E4's exit rules that would close it on this mark (rule names)
    exit_rules_handled: tuple[str, ...] = ()  # rules the day's daily run already ordered (same session)

    @property
    def short_strikes(self) -> tuple[float, ...]:
        return tuple(sorted({w.leg.strike for w in self.legs if not w.leg.bought}))

    @property
    def nearest_expiry(self) -> date:
        return min(w.expiry for w in self.legs)


@dataclass(frozen=True)
class Condition:
    """One thing found on a mark. `key` names it for the alert limits (same key, same alert); `facts` is the alert's
    second line, with no contract price."""

    check: str
    severity: str
    scope: str
    key: str
    repeat: str
    facts: str
    trade_id: str = ""
    information_only: bool = False  # an exit rule reached: information, no action


@dataclass(frozen=True)
class MarkFindings:
    mark: MonitorMark
    positions: int
    conditions: tuple[Condition, ...] = field(default_factory=tuple)
