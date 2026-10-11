"""Portfolio rules every new paper trade must pass. Returns a reason when a trade is not allowed."""

from __future__ import annotations

from datetime import datetime, timedelta

from .. import journal
from ..constants import SessionPhase, TradeStatus
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
