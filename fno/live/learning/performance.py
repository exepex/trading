"""Track-record checks on closed trades: the automatic stop, and the go-live readiness test."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime

from ...constants import TradeStatus


def closed_trades(trades: list[dict]) -> list[dict]:
    return sorted((t for t in trades if t["status"] == TradeStatus.CLOSED.value), key=lambda t: t["closed_at"])


def max_drawdown(pnls: list[float]) -> float:
    """Largest fall in cumulative net P&L from a previous peak (rupees, positive)."""
    equity = peak = worst = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        worst = max(worst, peak - equity)
    return worst


def current_drawdown(pnls: list[float]) -> float:
    """How far cumulative net P&L is below its best point right now (rupees, positive)."""
    equity = peak = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
    return peak - equity


def performance_stop_reason(trades: list[dict], cfg: dict, since: datetime | None = None) -> str | None:
    """Why the whole experiment should stop for review: a losing recent run, or being deep below the best point.
    `since` (the last manual release of the kill switch) restarts the count, so a reviewed stop does not re-fire
    on the same history; a recovered drawdown no longer counts."""
    rules = cfg.get("performance_kill", {})
    closed = closed_trades(trades)
    if since is not None:
        closed = [t for t in closed if datetime.fromisoformat(t["closed_at"]) > since]
    pnls = [t["pnl_net"] for t in closed]
    window = rules.get("rolling_trades", 20)
    if len(pnls) >= window and sum(pnls[-window:]) < 0:
        return f"the last {window} trades lost Rs {-sum(pnls[-window:]):,.0f} in total"
    limit = rules.get("max_drawdown")
    if limit and current_drawdown(pnls) >= limit:
        return f"Rs {current_drawdown(pnls):,.0f} below the best point (limit Rs {limit:,.0f})"
    return None


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    passed: bool
    detail: str


def readiness_checks(trades: list[dict], cfg: dict, today: date) -> list[ReadinessCheck]:
    """The go-live test from config.yaml go_live_criteria. All must pass before any real money."""
    rules = cfg.get("go_live_criteria", {})
    done = closed_trades(trades)
    pnls = [t["pnl_net"] for t in done]
    n = len(pnls)
    first_day = date.fromisoformat(done[0]["opened_at"][:10]) if done else today
    weeks = (today - first_day).days / 7
    mean = sum(pnls) / n if n else 0.0
    spread = math.sqrt(sum((p - mean) ** 2 for p in pnls) / (n - 1)) if n > 1 else 0.0
    t_stat = mean / (spread / math.sqrt(n)) if spread else 0.0
    wins, losses = sum(p for p in pnls if p > 0), -sum(p for p in pnls if p < 0)
    profit_factor = wins / losses if losses else (math.inf if wins else 0.0)
    drawdown = max_drawdown(pnls)  # the worst fall ever counts for go-live, even if it later recovered
    capital = cfg.get("account", {}).get("capital", 0)
    drawdown_limit = capital * rules["max_drawdown_pct"] / 100 if "max_drawdown_pct" in rules else math.inf
    return [
        ReadinessCheck(
            "closed trades", n >= rules.get("min_closed_trades", 100), f"{n} of {rules.get('min_closed_trades', 100)}"
        ),
        ReadinessCheck(
            "weeks of paper trading",
            weeks >= rules.get("min_trading_weeks", 13),
            f"{weeks:.1f} of {rules.get('min_trading_weeks', 13)}",
        ),
        ReadinessCheck("net profit after all charges", sum(pnls) > 0, f"Rs {sum(pnls):,.0f}"),
        ReadinessCheck(
            "statistical confidence (t-stat)",
            t_stat >= rules.get("min_t_stat", 2.0),
            f"{t_stat:.2f}, need {rules.get('min_t_stat', 2.0)}",
        ),
        ReadinessCheck(
            "profit factor",
            profit_factor >= rules.get("min_profit_factor", 1.3),
            f"{profit_factor:.2f}, need {rules.get('min_profit_factor', 1.3)}",
        ),
        ReadinessCheck(
            "max drawdown",
            drawdown <= drawdown_limit,
            f"Rs {drawdown:,.0f}, limit Rs {drawdown_limit:,.0f} ({rules.get('max_drawdown_pct', 0):g}% of capital)",
        ),
    ]
