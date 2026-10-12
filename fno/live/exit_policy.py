"""When an open paper trade must be closed. Discipline first: these rules are never skipped."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from ..constants import ExitReason, SessionPhase
from .market_clock import MarketClock

PEAK_VALUE_FIELD = "peak_value"  # best per-unit value an open trade has reached, kept on the trade


@dataclass(frozen=True)
class TrailingStop:
    """Once a trade has gained `activate_gain_pct`, never give back more than (100 - lock_pct)% of its best gain."""

    activate_gain_pct: float = 30.0
    lock_pct: float = 50.0
    enabled: bool = True

    @classmethod
    def from_config(cls, cfg: dict) -> TrailingStop:
        return cls(**{k: v for k, v in (cfg or {}).items() if k in cls.__dataclass_fields__})

    def triggered(self, entry: float, peak: float, current: float) -> bool:
        if not self.enabled or entry <= 0 or peak <= entry:
            return False
        if (peak / entry - 1) * 100 < self.activate_gain_pct:
            return False
        floor = entry + (peak - entry) * self.lock_pct / 100
        return current <= floor


class ExitPolicy:
    def __init__(
        self,
        clock: MarketClock,
        max_holding_days: int = 2,
        exit_days_before_expiry: int = 1,
        trailing: TrailingStop | None = None,
    ):
        self.clock = clock
        self.max_holding_days = max_holding_days
        self.exit_days_before_expiry = exit_days_before_expiry
        self.trailing = trailing or TrailingStop(enabled=False)

    def exit_reason(self, trade: dict, current_value: float, now: datetime, phase: SessionPhase) -> ExitReason | None:
        """Checked every mark: stop and target first, then the time rules."""
        pnl_per_unit = current_value - trade["entry_value"]
        if pnl_per_unit <= -trade["stop_amount"]:
            return ExitReason.STOP_LOSS
        if pnl_per_unit >= trade["target_amount"]:
            return ExitReason.TARGET
        if self.trailing.triggered(trade["entry_value"], trade.get(PEAK_VALUE_FIELD, current_value), current_value):
            return ExitReason.TRAILING_STOP
        if phase is not SessionPhase.SQUARE_OFF:
            return None
        today = now.date()
        if self._last_day_before_expiry(date.fromisoformat(trade["expiry"]), today):
            return ExitReason.BEFORE_EXPIRY
        opened = datetime.fromisoformat(trade["opened_at"]).date()
        if self.clock.trading_days_held(opened, today) >= self.max_holding_days:
            return ExitReason.MAX_HOLDING_DAYS
        return None

    def _last_day_before_expiry(self, expiry: date, today: date) -> bool:
        """True from the last allowed trading day onwards; trades never stay into expiry day."""
        last_day = expiry
        for _ in range(self.exit_days_before_expiry):
            last_day = self.clock.previous_trading_day(last_day)
        return today >= last_day
