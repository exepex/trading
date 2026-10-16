"""The monitor's checks (story LM1, design 4.2): one class per condition (strategy pattern), each reading one mark and
the open positions and returning what it finds. They only describe: none can open, change or close a trade.

Market-wide conditions (the big move, stale quotes) are one condition for the whole desk, never one per position
(judge 215 note 2). No alert text names a contract's price: strikes and NIFTY's level are allowed."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, time, timedelta

from ..models import IST
from ..research_data.calendar import CalendarError, SessionCalendar
from .model import DANGER, DESK, HOURLY, ONCE, POSITION, WARNING, Condition, MonitorMark, WatchedPosition
from .settings import MonitorSettings

PRECISION = 6  # percent digits kept, so a level exactly at a threshold is not lost to float noise (1.4999...)
# E4's rule names (`fno/desk/exit_rules.py`, pinned by a test) in plain words: the monitor imports nothing of the desk
RULE_LABELS = {"profit_target": "profit target", "stop_loss": "stop loss", "time_exit": "time limit"}
# NSE's longest closure from 2017 to 2026 is 5 calendar days between sessions (2,478 sessions, the A7 calendar), so any
# 7 days hold a session: an expiry more than 7 x (N + 1) days away is more than N sessions away
DAYS_PER_SESSION_AT_MOST = 7
EXPIRY_UNCOUNTED = "expiry_uncounted"
REACHED = "{trade} ({book}) reached its {rule} rule at {when}; the paper record changes at the daily run"
WAITING_CHECKS = {
    "vix_jump": "waits for an intraday VIX source (A16's mark has none); nothing built, nothing sent",
    "weather_upgrade": "waits for an M1 intraday rule (M1 rates one record a session); nothing built, nothing sent",
}


class MonitorCheck(ABC):
    name: str

    def __init__(self, settings: MonitorSettings):
        self.settings = settings

    @abstractmethod
    def find(self, mark: MonitorMark, positions: list[WatchedPosition]) -> list[Condition]:
        """The conditions true on this mark (the mark is usable: its index level is known)."""


class LossUsed(MonitorCheck):
    """The loss if closed at the touch against the maximum loss fixed at entry; an unmarked position says so."""

    name = "loss_used"

    def find(self, mark, positions):
        return [c for p in positions if (c := self._one(p))]

    def _one(self, p: WatchedPosition) -> Condition | None:
        if p.loss_now_rs is None:
            facts = f"{p.trade_id} ({p.book}): a leg is not on this mark, so its loss cannot be measured"
            return Condition("cannot_mark", WARNING, POSITION, f"cannot_mark:{p.trade_id}", HOURLY, facts, p.trade_id)
        if p.max_loss_rs <= 0:
            return None  # a position that can no longer lose
        share = p.loss_now_rs / p.max_loss_rs
        level = next((s for s, limit in self._levels() if share >= limit), None)
        if level is None:
            return None
        facts = (f"{p.trade_id} ({p.book}): loss used {share:.0%} of its maximum "
                 f"(Rs {p.loss_now_rs:,.0f} of Rs {p.max_loss_rs:,.0f})")  # fmt: skip
        return Condition(self.name, level, POSITION, f"{self.name}:{level}:{p.trade_id}", HOURLY, facts, p.trade_id)

    def _levels(self):
        return ((DANGER, self.settings.loss_used_danger), (WARNING, self.settings.loss_used_warning))


class ShortStrikeNear(MonitorCheck):
    name = "short_strike_near"

    def find(self, mark, positions):
        found = []
        for p in positions:
            for strike in p.short_strikes:
                gap = round(abs(mark.index_level - strike) / mark.index_level * 100, PRECISION)
                if gap <= self.settings.short_strike_near_pct:
                    level = f"NIFTY {mark.index_level:,.2f}"
                    facts = f"{p.trade_id} ({p.book}): {level} is {gap:.2f}% from short strike {strike:,.0f}"
                    found.append(Condition(self.name, DANGER, POSITION, f"{self.name}:{p.trade_id}:{strike:g}", HOURLY,
                                           facts, p.trade_id))  # fmt: skip
        return found


class ExitRuleReached(MonitorCheck):
    """Information only (E8 keeps the one action alert); quiet about a rule the day's daily run already ordered."""

    name = "exit_rule_reached"

    def find(self, mark, positions):
        when = f"{mark.mark.astimezone(IST):%H:%M} IST"
        return [
            Condition(
                self.name,
                DANGER,
                POSITION,
                f"{self.name}:{p.trade_id}:{rule}",
                ONCE,
                REACHED.format(trade=p.trade_id, book=p.book, rule=RULE_LABELS[rule], when=when),
                p.trade_id,
                information_only=True,
            )  # fmt: skip
            for p in positions
            for rule in p.exit_rules_reached
            if rule not in p.exit_rules_handled
        ]


class BigMove(MonitorCheck):
    """NIFTY far from the previous session's level: once per further step when a step is set, else hourly."""

    name = "big_move"

    def find(self, mark, positions):
        if not mark.previous_close:
            return []
        move = round((mark.index_level / mark.previous_close - 1) * 100, PRECISION)
        if abs(move) < self.settings.big_move_pct:
            return []
        way = "above" if move > 0 else "below"
        facts = (f"NIFTY {mark.index_level:,.2f} is {abs(move):.2f}% {way} the previous session's level "
                 f"{mark.previous_close:,.2f}; {len(positions)} open positions")  # fmt: skip
        step = self.settings.big_move_step_pct
        if step is None:
            return [Condition(self.name, DANGER, DESK, f"{self.name}:{way}", HOURLY, facts)]
        reached = (
            self.settings.big_move_pct + int(round((abs(move) - self.settings.big_move_pct) / step, PRECISION)) * step
        )
        return [Condition(self.name, DANGER, DESK, f"{self.name}:{way}:{reached:.2f}", ONCE, facts)]


class ExpiryNear(MonitorCheck):
    name = "expiry_near"

    def __init__(self, settings: MonitorSettings, calendar: SessionCalendar):
        super().__init__(settings)
        self.calendar = calendar

    def find(self, mark, positions):
        if mark.mark.astimezone(IST).time() < time.fromisoformat(self.settings.expiry_warn_from):
            return []
        return [c for p in positions if (c := self._one(mark, p))]

    def _one(self, mark: MonitorMark, p: WatchedPosition) -> Condition | None:
        expiry = p.nearest_expiry
        if (expiry - mark.session).days > DAYS_PER_SESSION_AT_MOST * (self.settings.expiry_warn_sessions + 1):
            return None  # too far to be within the window: no session count, so no calendar needed (judge 264)
        key = f"{self.name}:{p.trade_id}:{expiry}"
        try:
            left = len(self.calendar.sessions(mark.session, expiry)) - 1
        except CalendarError as gap:  # this position's warning only; every other check still runs
            facts = (
                f"{p.trade_id} ({p.book}): nearest expiry {expiry:%d %b %Y}; sessions to it cannot be counted: {gap}"
            )
            return Condition(EXPIRY_UNCOUNTED, WARNING, POSITION, key, ONCE, facts, p.trade_id)
        if not 0 <= left <= self.settings.expiry_warn_sessions:
            return None
        facts = f"{p.trade_id} ({p.book}): nearest expiry {expiry:%d %b %Y}, {left} sessions after today"
        return Condition(self.name, WARNING, POSITION, key, ONCE, facts, p.trade_id)


class QuotesStale:
    """No usable mark for the set minutes: one WARNING for the desk. Runs on every mark, usable or not."""

    name = "quotes_stale"

    def __init__(self, settings: MonitorSettings):
        self.settings = settings

    def find(self, mark: MonitorMark, session_start: datetime) -> list[Condition]:
        since = mark.last_good_at or session_start
        minutes = int((mark.mark - since) / timedelta(minutes=1))
        if minutes < self.settings.stale_after_minutes:
            return []
        facts = f"no usable quote mark for {minutes} minutes (this mark: {mark.status})"
        return [Condition(self.name, WARNING, DESK, self.name, HOURLY, facts)]
