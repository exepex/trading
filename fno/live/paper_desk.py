"""Opens, re-prices and closes live paper trades in their own journal file."""

from __future__ import annotations

import threading
from datetime import date, datetime
from pathlib import Path

from .. import journal
from ..constants import ExitReason, SessionPhase, TradeStatus
from ..providers import Provider
from .exit_policy import ExitPolicy
from .models import TradeIdea


class PaperDesk:
    def __init__(self, journal_path: Path, cfg: dict, chain_source: Provider, exit_policy: ExitPolicy):
        self.journal_path = journal_path
        self.cfg = cfg
        self.chain_source = chain_source
        self.exit_policy = exit_policy
        self.slippage = cfg.get("liquidity", {}).get("slippage_pct", 0.5)
        self._lock = threading.Lock()

    def trades(self) -> list[dict]:
        return journal.load(self.journal_path)

    def open_trades(self) -> list[dict]:
        return [t for t in self.trades() if t["status"] == TradeStatus.OPEN.value]

    def open(self, idea: TradeIdea, note: str = "") -> dict:
        with self._lock:
            trades = self.trades()
            trade = journal.open_trade(trades, idea.to_journal_candidate(), self.cfg, lots=idea.lots, note=note)
            trade["contract_name"] = idea.contract_name
            journal.save(trades, self.journal_path)
            return trade

    def review_open_trades(self, now: datetime, phase: SessionPhase) -> tuple[list[dict], list[str]]:
        """Re-price every open trade and close those an exit rule calls for. Returns (closed trades, errors)."""
        closed, errors = [], []
        with self._lock:
            trades = self.trades()
            for trade in trades:
                if trade["status"] != TradeStatus.OPEN.value:
                    continue
                try:
                    if self._review(trade, now, phase):
                        closed.append(trade)
                except Exception as exc:  # one bad quote must not stop the others being checked
                    errors.append(f"{trade['id']} {trade.get('contract_name', '')}: {exc}")
            journal.save(trades, self.journal_path)
        return closed, errors

    def close_all(self, reason: ExitReason) -> list[dict]:
        closed = []
        with self._lock:
            trades = self.trades()
            for trade in trades:
                if trade["status"] == TradeStatus.OPEN.value:
                    value, orders, spot = journal.close_value(trade, self.chain_source, self.slippage)
                    journal.finalise_trade(trade, value, orders, reason.value, self.cfg, spot)
                    closed.append(trade)
            journal.save(trades, self.journal_path)
        return closed

    def closed_on(self, day: date) -> list[dict]:
        return [
            t
            for t in self.trades()
            if t["status"] == TradeStatus.CLOSED.value and t.get("closed_at", "")[:10] == day.isoformat()
        ]

    def _review(self, trade: dict, now: datetime, phase: SessionPhase) -> bool:
        value, orders, spot = journal.close_value(trade, self.chain_source, self.slippage)
        units = trade["lot_size"] * trade["lots"]
        trade["last_mark"] = {
            "at": now.isoformat(timespec="minutes"),
            "spot": spot,
            "value": round(value, 2),
            "pnl": round((value - trade["entry_value"]) * units, 2),
        }
        reason = self.exit_policy.exit_reason(trade, value, now, phase)
        if reason is None:
            return False
        journal.finalise_trade(trade, value, orders, reason.value, self.cfg, spot)
        return True
