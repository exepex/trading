"""When an open paper trade must be closed. Discipline first: these rules are never skipped."""

from __future__ import annotations

from datetime import date, datetime

from ..constants import ExitReason, SessionPhase
from .market_clock import MarketClock


class ExitPolicy:
    def __init__(self, clock: MarketClock, max_holding_days: int = 2, exit_days_before_expiry: int = 1):
        self.clock = clock
        self.max_holding_days = max_holding_days
        self.exit_days_before_expiry = exit_days_before_expiry

    def exit_reason(self, trade: dict, current_value: float, now: datetime, phase: SessionPhase) -> ExitReason | None:
        """Checked every mark: stop and target first, then the time rules."""
        pnl_per_unit = current_value - trade["entry_value"]
        if pnl_per_unit <= -trade["stop_amount"]:
            return ExitReason.STOP_LOSS
        if pnl_per_unit >= trade["target_amount"]:
            return ExitReason.TARGET
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
