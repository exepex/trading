"""Daily research brief: scan underlyings, score setups, write Markdown + JSON."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from .models import MarketContext, OptionChain, now_ist
from .providers import Provider
from .signals import Signals, compute_signals
from .strategies import Candidate, build_candidates, confidence_label, select

NAMES = {
    "bull_call_spread": "Bull call spread",
    "bear_put_spread": "Bear put spread",
    "long_call": "Long call",
    "long_put": "Long put",
    "iron_condor": "Iron condor",
}


@dataclass
class ExpiryScan:
    expiry: str
    dte: int
    signals: Signals
    candidates: list[Candidate]
    selected: list[Candidate]
    oi_profile: list[tuple[float, float, float]] = field(default_factory=list)  # strike, call OI, put OI


@dataclass
class UnderlyingScan:
    underlying: str
    spot: float
    day_change_pct: float | None
    vix: float | None
    as_of: str
    lot_size: int
    expiries: list[ExpiryScan] = field(default_factory=list)
    error: str | None = None
    context: MarketContext | None = None


def oi_profile(chain: OptionChain, n: int = 9) -> list[tuple[float, float, float]]:
    """Call and put open interest for n strikes either side of the money."""
    strikes = chain.strikes()
    i = strikes.index(chain.atm_strike())
    out = []
    for k in strikes[max(0, i - n) : i + n + 1]:
        ce, pe = chain.get(k, "CE"), chain.get(k, "PE")
        out.append((k, ce.oi if ce else 0.0, pe.oi if pe else 0.0))
    return out


def scan_underlying(provider: Provider, underlying: str, cfg: dict) -> UnderlyingScan:
    exp_cfg = cfg.get("expiry", {})
    today = now_ist().date()
    expiries = [
        e for e in provider.expiries(underlying) if exp_cfg.get("min_dte", 3) <= (e - today).days <= exp_cfg.get("max_dte", 35)
    ][: exp_cfg.get("max_expiries_per_underlying", 2)]
    ctx = provider.context(underlying)
    scan = UnderlyingScan(underlying, ctx.spot, ctx.day_change_pct, ctx.vix, "", provider.fallback_lot_size(underlying))
    scan.context = ctx
    if not expiries:
        scan.error = "no expiry inside the configured days-to-expiry window"
        return scan
    for exp in expiries:
        chain = provider.chain(underlying, exp)
        scan.spot = chain.spot or scan.spot
        scan.as_of = chain.timestamp.strftime("%d %b %Y %H:%M IST")
        scan.lot_size = chain.lot_size
        sig = compute_signals(ctx, chain, cfg)
        cands = build_candidates(chain, sig, cfg)
        scan.expiries.append(
            ExpiryScan(exp.isoformat(), (exp - today).days, sig, cands, select(cands, sig), oi_profile(chain))
        )
    return scan


def _rs(x: float) -> str:
    return "unlimited" if math.isinf(x) else f"Rs {x:,.0f}"


def _pick(scans: list[UnderlyingScan]) -> tuple[Candidate | None, Signals | None]:
    best: tuple[Candidate, Signals] | None = None
    for s in scans:
        for e in s.expiries:
            if e.selected and (best is None or e.selected[0].score > best[0].score):
                best = (e.selected[0], e.signals)
    return best if best else (None, None)


def _candidate_md(c: Candidate, sig: Signals, capital: float) -> list[str]:
    lot = c.lot_size
    legs = ", ".join(f"{l.side.upper()} {int(l.strike)} {l.kind} @ {l.price:.2f}" for l in c.legs)
    kind = "debit" if c.entry_value > 0 else "credit"
    lines = [
        f"**{NAMES[c.strategy]}: {c.underlying} {c.expiry} ({c.dte} days)**, id `{c.id}`",
        "",
        f"- Legs: {legs}",
        f"- Net {kind}: {abs(c.entry_value):.2f} per unit = Rs {abs(c.entry_value) * lot:,.0f} per lot ({lot} units)",
        f"- Max profit: {_rs(c.max_profit * lot) if not math.isinf(c.max_profit) else 'unlimited'} per lot; "
        f"max loss: Rs {c.max_loss * lot:,.0f} per lot; breakeven: {', '.join(f'{b:,.0f}' for b in c.breakevens) or 'n/a'}",
        f"- Market-implied chance of profit at expiry: {c.pop_market * 100:.0f}%",
        f"- Exit plan: take profit at +Rs {c.target_amount * lot:,.0f}/lot, stop at -Rs {c.stop_amount * lot:,.0f}/lot, "
        "and close the day before expiry regardless",
        f"- Size: {c.lots} lot(s). Planned risk Rs {c.risk_per_lot:,.0f}/lot incl. ~Rs {c.charges_per_lot:,.0f} charges; "
        f"worst case Rs {c.worst_case_per_lot:,.0f}/lot ({c.worst_case_per_lot / capital * 100:.1f}% of capital)",
    ]
    for n in c.notes:
        lines.append(f"- Note: {n}")
    return lines


def render_markdown(scans: list[UnderlyingScan], cfg: dict) -> str:
    capital = cfg.get("account", {}).get("capital", 1)
    now = now_ist()
    lines = [
        f"# F&O research brief, {now:%a %d %b %Y}",
        "",
        f"Generated {now:%H:%M} IST from `{cfg.get('provider')}` data. Paper-trading experiment; "
        f"capital Rs {capital:,.0f}, risk budget {cfg.get('account', {}).get('risk_per_trade_pct')}% per trade.",
        "",
    ]
    pick, pick_sig = _pick(scans)
    lines.append("## Bottom line")
    lines.append("")
    if pick and confidence_label(pick_sig) != "low":
        lines.append(
            f"Top setup: **{NAMES[pick.strategy]} on {pick.underlying} ({pick.expiry})**. "
            f"Signal confidence: **{confidence_label(pick_sig)}** (bias {pick_sig.bias:+.2f}, "
            f"{pick_sig.agreement * 100:.0f}% of signals agree)."
        )
        lines.append("")
        lines += _candidate_md(pick, pick_sig, capital)
    elif pick:
        lines.append(
            f"**No trade.** The best setup ({NAMES[pick.strategy]} on {pick.underlying}) comes from a "
            f"low-confidence signal (bias {pick_sig.bias:+.2f}). Sitting out is a valid position."
        )
    else:
        lines.append("**No trade.** Signals are neutral or mixed, and no setup passed the filters.")
    lines.append("")

    for s in scans:
        lines.append(f"## {s.underlying}")
        lines.append("")
        if s.error:
            lines.append(f"Skipped: {s.error}.")
            lines.append("")
            continue
        chg = f" ({s.day_change_pct:+.2f}% on the day)" if s.day_change_pct is not None else ""
        vix = f", India VIX {s.vix:.2f}" if s.vix else ""
        lines.append(f"Spot **{s.spot:,.2f}**{chg}{vix}. Data as of {s.as_of}. Lot size {s.lot_size}.")
        lines.append("")
        for e in s.expiries:
            sig = e.signals
            lines.append(f"### Expiry {e.expiry} ({e.dte} days)")
            lines.append("")
            lines.append(
                f"Bias **{sig.label}** ({sig.bias:+.2f}), confidence **{confidence_label(sig)}**. "
                f"ATM IV {sig.atm_iv * 100 if sig.atm_iv else float('nan'):.1f}% vs 20-day realised "
                f"{sig.hv20 * 100 if sig.hv20 else float('nan'):.1f}%: options look **{sig.vol_regime}**."
            )
            lines.append("")
            lines.append("| Signal | Score | Reading |")
            lines.append("|---|---:|---|")
            for c in sig.components:
                lines.append(f"| {c.name} | {c.score:+.2f} | {c.detail} |")
            lines.append("")
            sup = ", ".join(f"{k:,.0f}" for k, _ in sig.support)
            res = ", ".join(f"{k:,.0f}" for k, _ in sig.resistance)
            em = f"+/-{sig.expected_move:,.0f}" if sig.expected_move else "n/a"
            pcr = f"{sig.pcr:.2f}" if sig.pcr is not None else "n/a"
            lines.append(
                f"OI support (put walls): {sup or 'n/a'}. OI resistance (call walls): {res or 'n/a'}. "
                f"Max pain {sig.max_pain:,.0f}. PCR {pcr}. Straddle-implied move by expiry {em}."
            )
            lines.append("")
            if e.selected:
                lines.append("Setups that fit the signal, best first:")
                lines.append("")
                for c in e.selected[:2]:
                    lines += _candidate_md(c, sig, capital)
                    lines.append("")
            else:
                lines.append("No setup matches this signal and passes the liquidity filters.")
                lines.append("")

    lines += [
        "## How to read this",
        "",
        "- **Bias** blends trend, momentum, RSI, put/call OI ratio and position between OI walls. "
        "It is a weighted heuristic, not a prediction.",
        "- **Chance of profit** uses the option market's own implied volatility. A setup can be worth taking "
        "below 50% if the payoff is asymmetric.",
        "- Prices assume you buy at the ask and sell at the bid. Real fills may be better or worse.",
        "- Log a setup with `python -m fno paper open <id>` to track it. You place real orders yourself on Groww.",
        "",
    ]
    return "\n".join(lines)


def slack_text(scans: list[UnderlyingScan], cfg: dict, journal_stats: dict | None = None) -> str:
    """Short Slack message that summarises the brief; the full HTML report is attached."""
    now = now_ist()
    pick, sig = _pick(scans)
    lines = [f"*F&O Market Brief, {now:%a %d %b %Y}*"]
    for s in scans:
        if s.error or not s.expiries:
            lines.append(f"• {s.underlying}: skipped ({s.error})")
            continue
        g = s.expiries[0].signals
        chg = f" ({s.day_change_pct:+.2f}%)" if s.day_change_pct is not None else ""
        lines.append(
            f"• {s.underlying} {s.spot:,.0f}{chg}: *{g.label}* (bias {g.bias:+.2f}, confidence {confidence_label(g)}), "
            f"options look {g.vol_regime}"
        )
    if s := next((x for x in scans if x.as_of and now.strftime("%d %b %Y") not in x.as_of), None):
        lines.append(f"_Data is from {s.as_of}; the market may be closed today._")
    if pick and confidence_label(sig) != "low":
        lot = pick.lot_size
        legs = ", ".join(f"{l.side.upper()} {int(l.strike)} {l.kind} @ {l.price:.2f}" for l in pick.legs)
        lines += [
            "",
            f"*Top setup:* {NAMES[pick.strategy]} on {pick.underlying}, expiry {pick.expiry}",
            f"{legs}",
            f"Cost Rs {abs(pick.entry_value) * lot:,.0f}/lot · max loss Rs {pick.max_loss * lot:,.0f} · "
            f"max profit {_rs(pick.max_profit * lot)} · chance of profit {pick.pop_market * 100:.0f}%",
            f"Stop -Rs {pick.stop_amount * lot:,.0f} · target +Rs {pick.target_amount * lot:,.0f} · size {pick.lots} lot(s)",
            f"Paper-trade id: `{pick.id}`",
        ]
    else:
        lines += ["", "*No trade today.* Signals are weak or mixed."]
    if journal_stats:
        j = journal_stats
        lines += [
            "",
            f"*Paper scorecard:* {j['closed']} closed ({j['win_rate']:.0f}% wins), net Rs {j['net']:,.0f}; "
            f"{j['open']} open (unrealised Rs {j['unrealised']:,.0f})",
        ]
    lines.append("_Research aid only, not advice. Report pages are attached as images below._")
    return "\n".join(lines)


def run_brief(provider: Provider, cfg: dict, out_dir: str | Path = "reports", journal_stats: dict | None = None,
              journal_log: list[str] | None = None) -> tuple[Path, Path, list[UnderlyingScan]]:
    scans = []
    for u in cfg.get("underlyings", []):
        try:
            scans.append(scan_underlying(provider, u, cfg))
        except Exception as exc:  # keep the brief going if one underlying fails
            scans.append(UnderlyingScan(u, 0, None, None, "", 0, error=f"data error: {exc}"))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = now_ist().strftime("%Y-%m-%d")
    md_path = out / f"{stamp}-brief.md"
    json_path = out / f"{stamp}-candidates.json"
    md_path.write_text(render_markdown(scans, cfg), encoding="utf-8")
    from .html_report import render_html

    html_path = out / f"{stamp}-brief.html"
    html_path.write_text(render_html(scans, cfg, journal_stats, journal_log), encoding="utf-8")
    # Body-only variant for publishing as a claude.ai Artifact page.
    (out / f"{stamp}-page.html").write_text(render_html(scans, cfg, journal_stats, journal_log, fragment=True), encoding="utf-8")
    from .snapshot import snapshot, split_png

    for old in out.glob(f"{stamp}-brief-*of*.png"):
        old.unlink()
    if snapshot(html_path, out / f"{stamp}-brief.png"):
        split_png(out / f"{stamp}-brief.png")
    (out / f"{stamp}-slack.md").write_text(slack_text(scans, cfg, journal_stats), encoding="utf-8")
    payload = {
        "generated": now_ist().isoformat(),
        "provider": cfg.get("provider"),
        "candidates": [c.to_dict() for s in scans for e in s.expiries for c in e.candidates],
    }
    json_path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return md_path, json_path, scans
