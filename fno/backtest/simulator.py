"""Walks past 5-minute bars one at a time, exactly as the live desk would see them, and paper-trades one modelled
option per underlying with the desk's own rules, guards, exits and charges."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from ..constants import Direction, OptionKind, SessionPhase
from ..costs import legs_charges
from ..live.exit_policy import PEAK_VALUE_FIELD, ExitPolicy
from ..live.market_clock import MarketClock
from ..live.market_view import MarketViewBuilder
from ..live.models import Candle, UnderlyingSnapshot
from ..live.research.research_context import ResearchSnapshot
from ..live.signals.base import SymbolInputs
from .option_model import OptionModel

PERCENT = 100.0
GRADE_AHEAD_BARS = 6  # a vote is graded against the move over the next 30 minutes
MIN_VOTE = 0.2  # weaker votes are not graded
HISTORY_SESSIONS = 4
BAR = timedelta(minutes=5)  # earlier sessions given to the rules (previous-day levels, normal volume)


@dataclass
class SimTrade:
    symbol: str
    direction: str
    kind: str
    strike: float
    opened_at: datetime
    entry: float
    lot_size: int
    sigma: float
    record: dict = field(default_factory=dict)  # the shape ExitPolicy reads
    exit_value: float | None = None
    exit_reason: str | None = None
    closed_at: datetime | None = None
    net_pnl: float = 0.0


@dataclass(frozen=True)
class Cooldowns:
    """Entry pauses per name: after any exit, and longer after a losing one (the desk's post-loss pause is
    account-wide; see the report's disclaimer)."""

    after_exit_minutes: float = 30
    after_loss_minutes: float = 45

    def blocks(self, last: SimTrade | None, now: datetime) -> bool:
        if last is None or last.closed_at is None:
            return False
        pause = max(self.after_exit_minutes, self.after_loss_minutes if last.net_pnl < 0 else 0)
        return now - last.closed_at < timedelta(minutes=pause)


@dataclass
class RuleGrade:
    hits: int = 0
    votes: int = 0


@dataclass
class BacktestResult:
    trades: list[SimTrade] = field(default_factory=list)
    grades: dict[str, RuleGrade] = field(default_factory=dict)
    sessions: int = 0
    unfinished: int = 0


def sessions_of(candles: list[Candle]) -> list[list[Candle]]:
    days: dict[date, list[Candle]] = {}
    for c in candles:
        days.setdefault(c.start.date(), []).append(c)
    return [days[d] for d in sorted(days)]


class Backtester:
    def __init__(
        self,
        builder: MarketViewBuilder,
        clock: MarketClock,
        exits: ExitPolicy,
        model: OptionModel,
        stop_pct: float,
        target_pct: float,
        charges: dict,
        cooldowns: Cooldowns | None = None,
    ):
        self.builder, self.clock, self.exits, self.model = builder, clock, exits, model
        self.cooldowns = cooldowns or Cooldowns()
        self.stop_pct, self.target_pct, self.charges = stop_pct, target_pct, charges

    def run(
        self, symbol: str, candles: list[Candle], lot_size: int, benchmark: list[Candle] | None = None
    ) -> BacktestResult:
        result = BacktestResult()
        sessions = sessions_of(candles)
        bench = {c.start: c.close for c in benchmark or []}
        open_trade: SimTrade | None = None
        last_closed: SimTrade | None = None
        for index in range(1, len(sessions)):
            today, history = sessions[index], [c for s in sessions[max(0, index - HISTORY_SESSIONS) : index] for c in s]
            previous_close = sessions[index - 1][-1].close
            bench_prev = self._previous_close(benchmark, today[0].start.date())
            result.sessions += 1
            for i, bar in enumerate(today):
                now = bar.start + BAR  # decisions are made when the bar has closed
                if open_trade is not None and self._manage(open_trade, bar.close, now):
                    result.trades.append(open_trade)
                    open_trade, last_closed = None, open_trade
                inputs = self._inputs(symbol, today[: i + 1], history, previous_close, bench, bench_prev, now)
                view = self.builder.build(inputs)
                self._grade(view.votes, today, i, result.grades)
                tradeable = view.direction is not Direction.NEUTRAL and not view.blocked
                allowed = not self.cooldowns.blocks(last_closed, now)
                if open_trade is None and tradeable and allowed and self.clock.phase(now) is SessionPhase.TRADING:
                    open_trade = self._open(symbol, view.direction, bar.close, now, lot_size, history + today[: i + 1])
        result.unfinished = int(open_trade is not None)  # still open when the data ends: not counted
        return result

    @staticmethod
    def _previous_close(benchmark: list[Candle] | None, day: date) -> float | None:
        earlier = [c.close for c in benchmark or [] if c.start.date() < day]
        return earlier[-1] if earlier else None

    @staticmethod
    def _inputs(symbol, today, history, previous_close, bench, bench_prev, now) -> SymbolInputs:
        last = today[-1]
        bench_now = bench.get(last.start)
        bench_change = (bench_now / bench_prev - 1) * PERCENT if bench_now and bench_prev else None
        return SymbolInputs(
            symbol=symbol,
            snapshot=UnderlyingSnapshot(symbol, last.close, previous_close),
            candles=today,
            benchmark_change_pct=bench_change,
            research=ResearchSnapshot(),
            now=now,
            history=history,
        )

    def _open(self, symbol, direction, spot, now, lot_size, closes_from) -> SimTrade:
        kind = OptionKind.CALL.value if direction is Direction.BULLISH else OptionKind.PUT.value
        sigma = self.model.sigma([c.close for c in closes_from])
        strike = self.model.atm_strike(symbol, spot)
        entry = self.model.price(spot, strike, self.model.days_to_expiry_at_entry, sigma, kind)
        trade = SimTrade(symbol, direction.value, kind, strike, now, entry, lot_size, sigma)
        trade.record = {
            "entry_value": entry,
            "stop_amount": entry * self.stop_pct / PERCENT,
            "target_amount": entry * self.target_pct / PERCENT,
            "opened_at": now.isoformat(),
            "expiry": "2999-12-31",  # expiry is modelled through days_left, never reached within the hold
            PEAK_VALUE_FIELD: entry,
        }
        return trade

    def _manage(self, trade: SimTrade, spot: float, now: datetime) -> bool:
        elapsed_days = (now - trade.opened_at).total_seconds() / 86400
        days_left = self.model.days_to_expiry_at_entry - elapsed_days
        value = self.model.price(spot, trade.strike, days_left, trade.sigma, trade.kind)
        trade.record[PEAK_VALUE_FIELD] = max(trade.record[PEAK_VALUE_FIELD], value)
        reason = self.exits.exit_reason(trade.record, value, now, self.clock.phase(now))
        if reason is None:
            return False
        units = trade.lot_size
        charges = legs_charges([("buy", trade.entry), ("sell", value)], units, self.charges)
        trade.exit_value, trade.exit_reason, trade.closed_at = value, reason.value, now
        trade.net_pnl = (value - trade.entry) * units - charges
        return True

    @staticmethod
    def _grade(votes, today: list[Candle], i: int, grades: dict[str, RuleGrade]) -> None:
        if i + GRADE_AHEAD_BARS >= len(today):
            return
        move = today[i + GRADE_AHEAD_BARS].close - today[i].close
        for vote in votes:
            if abs(vote.score) < MIN_VOTE or move == 0:
                continue
            grade = grades.setdefault(vote.rule, RuleGrade())
            grade.votes += 1
            grade.hits += vote.score * move > 0
