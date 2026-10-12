"""Paper-trading journal stored as JSON in the repo, so it survives between sessions."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from .config import ROOT
from .costs import CHARGE_NAMES, legs_breakdown, legs_charges
from .models import now_ist
from .providers import Provider

DEFAULT_PATH = ROOT / "journal" / "trades.json"


def load(path: Path = DEFAULT_PATH) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save(trades: list[dict], path: Path = DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trades, indent=1), encoding="utf-8")


def find_candidate(cand_id: str, reports_dir: Path) -> dict:
    for f in sorted(reports_dir.glob("*-candidates.json"), reverse=True):
        for c in json.loads(f.read_text(encoding="utf-8")).get("candidates", []):
            if c["id"] == cand_id:
                return c
    raise KeyError(f"Candidate {cand_id} not found in {reports_dir}; run `python -m fno brief` first.")


def deployed(trades: list[dict]) -> float:
    """Premium currently tied up in open trades."""
    return sum(abs(t["entry_value"]) * t["lot_size"] * t["lots"] for t in trades if t["status"] == "open")


def day_check(trades: list[dict], cfg: dict, today: date | None = None) -> str | None:
    """Reason to stop opening trades today, or None."""
    today = today or now_ist().date()
    lim = cfg.get("daily_limits", {})
    closed = sorted(
        (t for t in trades if t["status"] == "closed" and t.get("closed_at", "")[:10] == today.isoformat()),
        key=lambda t: t["closed_at"],
    )
    net = sum(t["pnl_net"] for t in closed)
    if net <= -lim.get("max_loss", float("inf")):
        return f"daily loss limit reached (net Rs {net:,.0f} today)"
    if net >= lim.get("profit_lock", float("inf")):
        return f"profit lock reached (net +Rs {net:,.0f} today): done for the day"
    n = lim.get("max_consecutive_losses", 0)
    if n and len(closed) >= n and all(t["pnl_net"] <= 0 for t in closed[-n:]):
        return f"{n} losing trades in a row today"
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    week_net = sum(
        t["pnl_net"] for t in trades if t["status"] == "closed" and t.get("closed_at", "")[:10] >= week_start
    )
    if week_net <= -lim.get("weekly_max_loss", float("inf")):
        return f"weekly loss limit reached (net Rs {week_net:,.0f} this week)"
    return None


def check_portfolio_limits(trades: list[dict], cand: dict, cfg: dict, lots: int) -> None:
    """Raise if opening this trade would break the open-trade, daily or deployment limits."""
    max_open = cfg.get("account", {}).get("max_open_trades", 5)
    if sum(t["status"] == "open" for t in trades) >= max_open:
        raise RuntimeError(f"Already {max_open} open trades (account.max_open_trades). Close one first.")
    stop = day_check(trades, cfg)
    if stop:
        raise RuntimeError(f"No new trades today: {stop}.")
    cost = abs(cand["entry_value"]) * cand["lot_size"] * lots
    rules = cfg.get("position_rules", {})
    cap = rules.get("max_deployed", float("inf"))
    if not cand.get("exception"):
        cap = min(cap, rules.get("normal_deployed", cap) * (1 + rules.get("budget_tolerance_pct", 10) / 100))
    if deployed(trades) + cost > cap:
        raise RuntimeError(
            f"Opening this (Rs {cost:,.0f}) would put Rs {deployed(trades) + cost:,.0f} in open trades, "
            f"over the Rs {cap:,.0f} limit."
        )


def open_trade(
    trades: list[dict], cand: dict, cfg: dict, lots: int | None = None, note: str = "", enforce_limits: bool = True
) -> dict:
    """Record a new paper trade. enforce_limits=False is only for the shadow book, which grades every idea."""
    lots = lots if lots is not None else (cand.get("lots") or 0)
    if lots < 1:
        raise RuntimeError("This setup does not fit the position rules (0 lots). See its notes.")
    if enforce_limits:
        check_portfolio_limits(trades, cand, cfg, lots)
    units = cand["lot_size"] * lots
    entry_orders = [(l["side"], l["price"]) for l in cand["legs"]]
    trade = {
        "id": f"T{len(trades) + 1:03d}",
        "candidate": cand["id"],
        "opened_at": now_ist().isoformat(timespec="minutes"),
        "underlying": cand["underlying"],
        "expiry": cand["expiry"],
        "strategy": cand["strategy"],
        "direction": cand["direction"],
        "spot_at_entry": cand["spot"],
        "legs": [{k: l[k] for k in ("kind", "strike", "side", "price")} for l in cand["legs"]],
        "lot_size": cand["lot_size"],
        "lots": lots,
        "entry_value": cand["entry_value"],
        "stop_amount": cand["stop_amount"],
        "target_amount": cand["target_amount"],
        "entry_charges": round(legs_charges(entry_orders, units, cfg.get("charges", {})), 2),
        "capital_used": round(abs(cand["entry_value"]) * units, 2),
        "charge_breakdown": {
            k: round(v, 2) for k, v in legs_breakdown(entry_orders, units, cfg.get("charges", {})).items()
        },
        "status": "open",
        "note": note,
        "last_mark": None,
    }
    trades.append(trade)
    return trade


def close_value(trade: dict, provider: Provider, slippage: float) -> tuple[float, list[tuple[str, float]], float]:
    """Current per-unit value of the position if closed now, the closing orders, and spot."""
    chain = provider.chain(trade["underlying"], date.fromisoformat(trade["expiry"]))
    value, orders = 0.0, []
    for leg in trade["legs"]:
        q = chain.get(leg["strike"], leg["kind"])
        close_side = "sell" if leg["side"] == "buy" else "buy"
        if q is None:
            raise KeyError(f"{leg['strike']} {leg['kind']} missing from chain")
        price = q.fill_price(close_side, slippage)
        orders.append((close_side, price))
        value += (1 if leg["side"] == "buy" else -1) * price
    return value, orders, chain.spot


def _intrinsic_value(trade: dict, spot: float) -> tuple[float, list[tuple[str, float]]]:
    value, orders = 0.0, []
    for leg in trade["legs"]:
        k = leg["strike"]
        intrinsic = max(spot - k, 0) if leg["kind"] == "CE" else max(k - spot, 0)
        value += (1 if leg["side"] == "buy" else -1) * intrinsic
        orders.append(("sell" if leg["side"] == "buy" else "buy", intrinsic))
    return value, orders


def finalise_trade(
    trade: dict, value: float, orders: list[tuple[str, float]], reason: str, cfg: dict, spot: float
) -> None:
    units = trade["lot_size"] * trade["lots"]
    exit_orders = [o for o in orders if o[1] > 0]
    exit_charges = legs_charges(exit_orders, units, cfg.get("charges", {}))
    breakdown = dict(trade.get("charge_breakdown") or {})
    for k, v in legs_breakdown(exit_orders, units, cfg.get("charges", {})).items():
        breakdown[k] = round(breakdown.get(k, 0.0) + v, 2)
    gross = (value - trade["entry_value"]) * units
    trade.update(
        status="closed",
        closed_at=now_ist().isoformat(timespec="minutes"),
        exit_value=round(value, 2),
        exit_reason=reason,
        spot_at_exit=spot,
        pnl_gross=round(gross, 2),
        charges=round(trade["entry_charges"] + exit_charges, 2),
        pnl_net=round(gross - trade["entry_charges"] - exit_charges, 2),
        charge_breakdown=breakdown,
    )


def mark(trades: list[dict], provider: Provider, cfg: dict, today: date | None = None) -> list[str]:
    """Re-price open trades and close those that hit stop, target or the time exit."""
    today = today or now_ist().date()
    slippage = cfg.get("liquidity", {}).get("slippage_pct", 0.5)
    exit_days = cfg.get("exits", {}).get("exit_days_before_expiry", 1)
    log = []
    for t in trades:
        if t["status"] != "open":
            continue
        expiry = date.fromisoformat(t["expiry"])
        if today > expiry:
            spot = provider.context(t["underlying"]).spot
            value, orders = _intrinsic_value(t, spot)
            finalise_trade(t, value, orders, "expired (settled at intrinsic, approx.)", cfg, spot)
            log.append(f"{t['id']} expired: net P&L Rs {t['pnl_net']:,.0f}")
            continue
        value, orders, spot = close_value(t, provider, slippage)
        pnl_unit = value - t["entry_value"]
        t["last_mark"] = {
            "at": now_ist().isoformat(timespec="minutes"),
            "spot": spot,
            "value": round(value, 2),
            "pnl": round(pnl_unit * t["lot_size"] * t["lots"], 2),
        }
        reason = None
        if pnl_unit <= -t["stop_amount"]:
            reason = "stop loss"
        elif pnl_unit >= t["target_amount"]:
            reason = "target"
        elif today >= expiry - timedelta(days=exit_days):
            reason = "time exit before expiry"
        if reason:
            finalise_trade(t, value, orders, reason, cfg, spot)
            log.append(f"{t['id']} closed on {reason}: net P&L Rs {t['pnl_net']:,.0f}")
        else:
            log.append(f"{t['id']} open: unrealised Rs {t['last_mark']['pnl']:,.0f} (spot {spot:,.1f})")
    return log


def close(trades: list[dict], trade_id: str, provider: Provider, cfg: dict, reason: str = "manual") -> dict:
    t = next((t for t in trades if t["id"] == trade_id and t["status"] == "open"), None)
    if t is None:
        raise KeyError(f"No open trade {trade_id}")
    value, orders, spot = close_value(t, provider, cfg.get("liquidity", {}).get("slippage_pct", 0.5))
    finalise_trade(t, value, orders, reason, cfg, spot)
    return t


def stats(trades: list[dict]) -> dict:
    closed = [t for t in trades if t["status"] == "closed"]
    pnl = [t["pnl_net"] for t in closed]
    wins = [p for p in pnl if p > 0]
    return {
        "closed": len(closed),
        "open": sum(t["status"] == "open" for t in trades),
        "wins": len(wins),
        "win_rate": len(wins) / len(closed) * 100 if closed else 0.0,
        "net": sum(pnl),
        "unrealised": sum((t.get("last_mark") or {}).get("pnl", 0) for t in trades if t["status"] == "open"),
    }


def report(trades: list[dict], capital: float) -> str:
    closed = [t for t in trades if t["status"] == "closed"]
    opened = [t for t in trades if t["status"] == "open"]
    lines = ["# Paper-trading scorecard", ""]
    if closed:
        pnl = [t["pnl_net"] for t in closed]
        wins = [p for p in pnl if p > 0]
        losses = [p for p in pnl if p <= 0]
        equity, peak, max_dd = 0.0, 0.0, 0.0
        for p in pnl:
            equity += p
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        gross = sum(t["pnl_gross"] for t in closed)
        used = sum(t.get("capital_used") or abs(t["entry_value"]) * t["lot_size"] * t["lots"] for t in closed)
        breakdown = {k: sum((t.get("charge_breakdown") or {}).get(k, 0.0) for t in closed) for k in CHARGE_NAMES}
        lines += [
            f"- Closed trades: {len(closed)} ({len(wins)} wins, {len(losses)} losses, "
            f"win rate {len(wins) / len(closed) * 100:.0f}%)",
            f"- Gross P&L: Rs {gross:,.0f}",
            "- Charges: " + ", ".join(f"{CHARGE_NAMES[k]} Rs {v:,.0f}" for k, v in breakdown.items() if v),
            f"- **Net P&L after all charges: Rs {sum(pnl):,.0f}** ({sum(pnl) / capital * 100:+.2f}% of capital)",
            f"- Net margin on money used: {sum(pnl) / used * 100:+.1f}%" if used else "- Net margin: n/a",
            f"- Average win Rs {avg_win:,.0f}, average loss Rs {avg_loss:,.0f}",
            f"- Expectancy per trade: Rs {sum(pnl) / len(pnl):,.0f}",
            f"- Total charges paid: Rs {sum(t['charges'] for t in closed):,.0f}",
            f"- Max drawdown: Rs {max_dd:,.0f}",
            "",
            "| Trade | Setup | Opened | Exit reason | Net P&L |",
            "|---|---|---|---|---:|",
        ]
        for t in closed:
            lines.append(
                f"| {t['id']} | {t['candidate']} | {t['opened_at'][:10]} | {t['exit_reason']} | {t['pnl_net']:,.0f} |"
            )
        if len(closed) < 20:
            lines += [
                "",
                f"_Only {len(closed)} closed trades so far. Wait for at least 20-30 before drawing conclusions._",
            ]
    else:
        lines.append("No closed trades yet.")
    lines.append("")
    if opened:
        lines += ["## Open trades", "", "| Trade | Setup | Lots | Unrealised |", "|---|---|---:|---:|"]
        for t in opened:
            u = t["last_mark"]["pnl"] if t.get("last_mark") else None
            lines.append(f"| {t['id']} | {t['candidate']} | {t['lots']} | {'' if u is None else f'{u:,.0f}'} |")
    return "\n".join(lines) + "\n"
