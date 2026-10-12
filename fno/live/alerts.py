"""Slack messages for the live desk: entries, exits, day summary and problems. Text only, short and exact."""

from __future__ import annotations

import logging
from datetime import date

from ..notify import SlackTarget
from .models import TradeIdea

log = logging.getLogger(__name__)

PAPER_TAG = "PAPER"
ENTRY_HEADER = ":large_green_circle: *{tag} BUY · {name}*"
EXIT_HEADER = ":checkered_flag: *{tag} EXIT · {name}* ({reason})"
SUMMARY_HEADER = ":bar_chart: *F&O desk, {day:%a %d %b}: day summary ({tag})*"
KILL_HEADER = ":octagonal_sign: *Kill switch engaged.* All paper trades closed; no new trades until released."
KILL_PARTIAL = (
    ":octagonal_sign: *Kill switch engaged.* No new trades until released. Could not close yet (no price): {trades}; "
    "retrying every review."
)
PROBLEM_HEADER = ":warning: *F&O desk problem:* {message}"


def rupees(value: float, signed: bool = False) -> str:
    sign = "+" if signed and value > 0 else ("-" if value < 0 else "")
    return f"{sign}Rs {abs(value):,.0f}"


def entry_message(idea: TradeIdea, trade_id: str) -> str:
    view = idea.view
    supporting = [
        v.reason for v in sorted(view.votes, key=lambda v: -abs(v.score * v.weight)) if v.score * view.score > 0
    ]
    lines = [
        ENTRY_HEADER.format(tag=PAPER_TAG, name=idea.contract_name),
        f"{idea.lots} lot(s) x {idea.lot_size} @ Rs {idea.entry_price:.2f} = {rupees(idea.capital_used)}"
        + (" (strong-evidence exception)" if idea.exception else ""),
        f"Stop Rs {idea.stop_price:.2f} · Target Rs {idea.target_price:.2f} · {idea.underlying} spot {idea.spot:,.2f}",
        f"View: {view.direction.value} {view.score:+.2f}, {view.agreement * 100:.0f}% of signals agree"
        + (", strong evidence" if view.strong_evidence else ""),
    ]
    lines += [f"• {reason}" for reason in supporting[:4]]
    lines.append(f"_Trade {trade_id}. Search Groww for: {idea.contract_name}_")
    return "\n".join(lines)


def exit_message(trade: dict) -> str:
    name = trade.get("contract_name", trade["candidate"])
    return "\n".join(
        [
            EXIT_HEADER.format(tag=PAPER_TAG, name=name, reason=trade["exit_reason"]),
            f"Entry Rs {trade['entry_value']:.2f} → exit Rs {trade['exit_value']:.2f} · {trade['lots']} lot(s)",
            f"Gross {rupees(trade['pnl_gross'], True)} · charges {rupees(trade['charges'])} · "
            f"*net {rupees(trade['pnl_net'], True)}*",
        ]
    )


def day_summary_message(day: date, closed_today: list[dict], still_open: list[dict], scans: int, ideas: int) -> str:
    net = sum(t["pnl_net"] for t in closed_today)
    wins = sum(t["pnl_net"] > 0 for t in closed_today)
    lines = [
        SUMMARY_HEADER.format(day=day, tag=PAPER_TAG),
        f"Scans {scans} · trade ideas {ideas} · trades closed {len(closed_today)} ({wins} won)",
        f"*Net P&L today after all charges: {rupees(net, True)}*",
    ]
    lines += [
        f"• {t.get('contract_name', t['candidate'])}: {rupees(t['pnl_net'], True)} ({t['exit_reason']})"
        for t in closed_today
    ]
    if still_open:
        lines.append(f"Held overnight: {', '.join(t.get('contract_name', t['candidate']) for t in still_open)}")
    if not closed_today and not still_open:
        lines.append("No trade met the rules today.")
    return "\n".join(lines)


class LiveAlerts:
    """Sends messages; never raises, so a Slack outage cannot stop trading discipline."""

    def __init__(self, target: SlackTarget):
        self.target = target

    def send(self, text: str) -> bool:
        if not self.target.configured:
            log.info("slack not configured; message:\n%s", text)
            return False
        try:
            self.target.post(text)
            return True
        except Exception as exc:
            log.error("slack post failed: %s", exc)
            return False

    def problem(self, message: str) -> bool:
        return self.send(PROBLEM_HEADER.format(message=message))

    def kill_switch(self, left_open: list[str] | None = None) -> bool:
        return self.send(KILL_PARTIAL.format(trades=", ".join(left_open)) if left_open else KILL_HEADER)
