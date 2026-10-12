"""Reproduces the 12 Oct 2026 chart-rule backtest, its controls and its loss bridges from frozen inputs.

Run from the repository root:  python research/2026-10-12-backtest/replay.py
Writes trades.csv, controls.csv, random_runs.csv and summary.json next to this file. No network access, no orders.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import random
import sys
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fno.backtest.cli import DEFAULT_SYMBOLS, PRICE_GUARDS  # noqa: E402
from fno.backtest.simulator import BAR, SimTrade  # noqa: E402
from fno.config import load_config  # noqa: E402
from fno.constants import Direction  # noqa: E402
from fno.costs import legs_charges  # noqa: E402
from fno.live.models import Candle  # noqa: E402
from fno.live.services import build_backtester  # noqa: E402

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
EXPECTED_SHA256 = {
    "candles.csv.gz": "d0adda55ef070623adc3b03bf5a357b157727dced75aeccdcfa02800ab5d3d85",
    "lot_sizes.json": "b4d05c8381ca543be7f48d7680063dc5d9985a9a1783263cff76b68f4df55669",
    "config.yaml": "cc6d55bde201034b475cb9a29067e98750d352b9724c8a0d226734d31be14742",
}
BENCHMARK = "BENCHMARK_NIFTY"
RANDOM_SEEDS = range(30)
FIRST_BAR_EXIT = time(9, 20)  # a stop decided when the 09:15-09:20 bar closes
OPENING_TEN_MINUTES_END = time(9, 25)  # first or second bar


def check_inputs() -> None:
    for name, digest in EXPECTED_SHA256.items():
        actual = hashlib.sha256((INPUTS / name).read_bytes()).hexdigest()
        if actual != digest:
            raise SystemExit(f"{name}: sha256 {actual} does not match the frozen {digest}")


def load_candles() -> dict[str, list[Candle]]:
    out: dict[str, list[Candle]] = {}
    with gzip.open(INPUTS / "candles.csv.gz", "rt") as f:
        for row in csv.DictReader(f):
            candle = Candle(
                datetime.fromisoformat(row["start"]),
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
                float(row["volume"]),
            )
            out.setdefault(row["symbol"], []).append(candle)
    return out


@dataclass
class FixedSigma:
    """The option model with one trade's own volatility, so a control changes only the direction."""

    model: object
    fixed: float

    def sigma(self, closes):
        return self.fixed

    def __getattr__(self, name):
        return getattr(self.model, name)


class Replay:
    def __init__(self):
        self.cfg = load_config(INPUTS / "config.yaml")
        self.tester = build_backtester(self.cfg, PRICE_GUARDS)
        self.candles = load_candles()
        self.lots = json.loads((INPUTS / "lot_sizes.json").read_text())
        self.index = {s: {c.start: i for i, c in enumerate(self.candles[s])} for s in DEFAULT_SYMBOLS}

    def entries(self) -> list[SimTrade]:
        """Every entry the rules made, closed or still open at the end of the data, in time order per name."""
        opened, real_open = [], self.tester._open

        def record(*args, **kwargs):
            trade = real_open(*args, **kwargs)
            opened.append(trade)
            return trade

        self.tester._open = record
        try:
            for symbol in DEFAULT_SYMBOLS:
                self.tester.run(symbol, self.candles[symbol], self.lots.get(symbol, 1), self.candles[BENCHMARK])
        finally:
            self.tester._open = real_open
        return opened

    def mark(self, trade: SimTrade, candle: Candle) -> tuple[float, float, float]:
        """Value at a candle's close, the charges of buying and selling, and the net result."""
        now = candle.start + BAR
        days = (now - trade.opened_at).total_seconds() / 86400
        model = self.tester.model
        value = model.price(candle.close, trade.strike, model.days_to_expiry_at_entry - days, trade.sigma, trade.kind)
        charges = legs_charges([("buy", trade.entry), ("sell", value)], trade.lot_size, self.tester.charges)
        return value, charges, (value - trade.entry) * trade.lot_size - charges

    def outcome(self, trade: SimTrade) -> dict:
        if trade.closed_at is not None:
            charges = (trade.exit_value - trade.entry) * trade.lot_size - trade.net_pnl
            return {"status": "closed", "exit_value": trade.exit_value, "charges": charges, "net": trade.net_pnl}
        value, charges, net = self.mark(trade, self.candles[trade.symbol][-1])
        return {"status": "open, marked at the last close", "exit_value": value, "charges": charges, "net": net}

    def replay(self, trade: SimTrade, direction: Direction) -> dict:
        candles = self.candles[trade.symbol]
        i = self.index[trade.symbol][trade.opened_at - BAR]
        model, self.tester.model = self.tester.model, FixedSigma(self.tester.model, trade.sigma)
        try:
            sim = self.tester._open(trade.symbol, direction, candles[i].close, trade.opened_at, trade.lot_size, [])
        finally:
            self.tester.model = model
        for candle in candles[i + 1 :]:
            if self.tester._manage(sim, candle.close, candle.start + BAR):
                return {"status": "closed", "net": sim.net_pnl}
        return {"status": "open, marked at the last close", "net": self.mark(sim, candles[-1])[2]}

    def opening_bridge(self, trade: SimTrade, last_exit: time) -> dict | None:
        """For a stop hit at the open after an overnight hold (exit no later than `last_exit`): where the loss arose.

        Boundaries are found explicitly: the last candle of the previous session and the first candle of the exit
        session (attribution is marked incomplete if that session has no 09:15 candle)."""
        if trade.exit_reason != "stop loss" or trade.closed_at.date() == trade.opened_at.date():
            return None
        if trade.closed_at.time() > last_exit:
            return None
        candles = self.candles[trade.symbol]
        day = trade.closed_at.date()
        session = [c for c in candles if c.start.date() == day]
        previous_close = [c for c in candles if c.start.date() < day][-1]
        first = session[0]
        if first.start.time() != time(9, 15):
            return {"incomplete": 1}
        model = self.tester.model

        def value(spot, now):
            days = (now - trade.opened_at).total_seconds() / 86400
            return model.price(spot, trade.strike, model.days_to_expiry_at_entry - days, trade.sigma, trade.kind)

        at_previous_close = value(previous_close.close, previous_close.start + BAR)
        at_open = value(first.open, first.start)
        units = trade.lot_size
        charges = legs_charges([("buy", trade.entry), ("sell", trade.exit_value)], units, self.tester.charges)
        return {
            "incomplete": 0,
            "before_the_previous_close": (at_previous_close - trade.entry) * units,
            "overnight_option_value_change": (at_open - at_previous_close) * units,  # price gap and time decay
            "open_to_exit": (trade.exit_value - at_open) * units,
            "charges": -charges,
            "net": trade.net_pnl,
        }


def main() -> None:
    check_inputs()
    run = Replay()
    entries = run.entries()
    picks = {
        "rules": lambda t, _: Direction(t.direction),
        "opposite": lambda t, _: Direction.BEARISH if t.direction == "bullish" else Direction.BULLISH,
        "always_bullish": lambda t, _: Direction.BULLISH,
        "always_bearish": lambda t, _: Direction.BEARISH,
    }
    trades, controls, totals = [], [], {}
    for n, trade in enumerate(entries, 1):
        trade_id = f"E{n:03d}"
        result = run.outcome(trade)
        trades.append(
            {
                "id": trade_id,
                "symbol": trade.symbol,
                "direction": trade.direction,
                "option": trade.kind,
                "strike": trade.strike,
                "lot_size": trade.lot_size,
                "sigma": round(trade.sigma, 6),
                "opened_at": trade.opened_at.isoformat(),
                "entry_price": round(trade.entry, 4),
                "closed_at": trade.closed_at.isoformat() if trade.closed_at else "",
                "exit_reason": trade.exit_reason or "",
                "status": result["status"],
                "exit_price": round(result["exit_value"], 4),
                "charges": round(result["charges"], 2),
                "net": round(result["net"], 2),
            }
        )
    for name, pick in picks.items():
        nets = []
        for n, trade in enumerate(entries, 1):
            result = run.replay(trade, pick(trade, None))
            nets.append(result["net"])
            controls.append(
                {"control": name, "id": f"E{n:03d}", "status": result["status"], "net": round(result["net"], 2)}
            )
        totals[name] = round(sum(nets), 2)
    random_runs = []
    for seed in RANDOM_SEEDS:
        rng = random.Random(seed)
        nets = [run.replay(t, rng.choice([Direction.BULLISH, Direction.BEARISH]))["net"] for t in entries]
        random_runs.append({"seed": seed, "net": round(sum(nets), 2), "wins": sum(x > 0 for x in nets)})
    opening = {}
    for name, last_exit in (("first_bar_stops", FIRST_BAR_EXIT), ("opening_ten_minute_stops", OPENING_TEN_MINUTES_END)):
        bridges = [b for b in (run.opening_bridge(t, last_exit) for t in entries) if b]
        opening[name] = {"count": len(bridges), **{k: round(sum(b[k] for b in bridges), 2) for k in bridges[0]}}
    closed = [t for t in trades if t["status"] == "closed"]
    still_open = [t for t in trades if t["status"] != "closed"]
    summary = {
        "entries": len(trades),
        "closed": len(closed),
        "still_open": len(still_open),
        "closed_net": round(sum(t["net"] for t in closed), 2),
        "open_positions_marked_net": round(sum(t["net"] for t in still_open), 2),
        "all_entries_net": round(sum(t["net"] for t in trades), 2),
        "controls": totals,
        "random_runs_sorted": sorted(r["net"] for r in random_runs),
        **opening,
    }
    for name, rows in (("trades", trades), ("controls", controls), ("random_runs", random_runs)):
        with open(HERE / f"{name}.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
