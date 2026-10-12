"""Portfolio rules every new paper trade must pass. Returns a reason when a trade is not allowed."""

from __future__ import annotations

from datetime import datetime, timedelta

from .. import journal
from ..constants import INDEX_UNDERLYINGS, SessionPhase, TradeStatus
from .kill_switch import KillSwitch
from .models import TradeIdea


class PortfolioGate:
    def __init__(self, cfg: dict, kill_switch: KillSwitch, reentry_cooldown_minutes: int = 30):
        self.cfg = cfg
        self.kill_switch = kill_switch
        self.cooldown = timedelta(minutes=reentry_cooldown_minutes)

    def refusal(self, idea: TradeIdea, trades: list[dict], phase: SessionPhase, now: datetime) -> str | None:
        """None if the idea may be opened now, otherwise the first rule it breaks."""
        checks = (
            self._kill_switch,
            self._session,
            self._open_slots,
            self._same_underlying,
            self._concentration,
            self._trade_frequency,
            self._loss_cooldown,
            self._recent_exit,
            self._daily_brakes,
            self._deployment,
        )
        for check in checks:
            reason = check(idea, trades, phase, now)
            if reason:
                return reason
        return None

    def _kill_switch(self, idea, trades, phase, now) -> str | None:
        return f"kill switch engaged: {self.kill_switch.reason}" if self.kill_switch.engaged else None

    def _session(self, idea, trades, phase, now) -> str | None:
        return None if phase is SessionPhase.TRADING else f"no new entries during '{phase.value}'"

    def _open_slots(self, idea, trades, phase, now) -> str | None:
        limit = self.cfg.get("account", {}).get("max_open_trades", 5)
        open_count = sum(t["status"] == TradeStatus.OPEN.value for t in trades)
        return f"{open_count} trades already open (max {limit})" if open_count >= limit else None

    def _same_underlying(self, idea, trades, phase, now) -> str | None:
        clash = any(t["status"] == TradeStatus.OPEN.value and t["underlying"] == idea.underlying for t in trades)
        return f"already holding a {idea.underlying} trade" if clash else None

    def _concentration(self, idea, trades, phase, now) -> str | None:
        """Several calls on NIFTY, BANKNIFTY and FINNIFTY are one bet: cap same-side and index exposure."""
        account = self.cfg.get("account", {})
        open_trades = [t for t in trades if t["status"] == TradeStatus.OPEN.value]
        same_side = sum(t.get("direction") == idea.view.direction.value for t in open_trades)
        if same_side >= account.get("max_same_direction", 3):
            return f"already {same_side} {idea.view.direction.value} trades open"
        if idea.underlying in INDEX_UNDERLYINGS:
            index_trades = sum(t["underlying"] in INDEX_UNDERLYINGS for t in open_trades)
            if index_trades >= account.get("max_index_trades", 2):
                return f"already {index_trades} index trades open"
        return None

    def _trade_frequency(self, idea, trades, phase, now) -> str | None:
        """Fewer, better trades: overtrading is where most retail F&O losses come from."""
        account = self.cfg.get("account", {})
        today = now.date()
        week_start = today - timedelta(days=today.weekday())
        opened_days = [datetime.fromisoformat(t["opened_at"]).date() for t in trades if t.get("opened_at")]
        per_day, per_week = account.get("max_new_trades_per_day", 2), account.get("max_new_trades_per_week", 8)
        if sum(d == today for d in opened_days) >= per_day:
            return f"already {per_day} new trades today"
        if sum(d >= week_start for d in opened_days) >= per_week:
            return f"already {per_week} new trades this week"
        return None

    def _loss_cooldown(self, idea, trades, phase, now) -> str | None:
        """A pause after any losing exit, so a loss is never chased with a hasty new trade."""
        minutes = self.cfg.get("account", {}).get("cooldown_after_loss_minutes", 0)
        losing_exits = [
            datetime.fromisoformat(t["closed_at"]) for t in trades if t.get("closed_at") and t.get("pnl_net", 0) < 0
        ]
        if minutes and losing_exits and now - max(losing_exits) < timedelta(minutes=minutes):
            return f"cooling off for {minutes} minutes after a losing trade"
        return None

    def _recent_exit(self, idea, trades, phase, now) -> str | None:
        for t in trades:
            closed_at = t.get("closed_at")
            if (
                t["underlying"] == idea.underlying
                and closed_at
                and now - datetime.fromisoformat(closed_at) < self.cooldown
            ):
                return f"exited {idea.underlying} less than {self.cooldown.seconds // 60} minutes ago"
        return None

    def _daily_brakes(self, idea, trades, phase, now) -> str | None:
        stop = journal.day_check(trades, self.cfg, now.date())
        return f"done for the day: {stop}" if stop else None

    def _deployment(self, idea, trades, phase, now) -> str | None:
        rules = self.cfg.get("position_rules", {})
        cap = rules.get("max_deployed", float("inf"))
        if not idea.exception:
            tolerance = 1 + rules.get("budget_tolerance_pct", 10) / 100
            cap = min(cap, rules.get("normal_deployed", cap) * tolerance)
        after = journal.deployed(trades) + idea.capital_used
        return f"would put Rs {after:,.0f} in open trades (limit Rs {cap:,.0f})" if after > cap else None
