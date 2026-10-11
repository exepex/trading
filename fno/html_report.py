"""Self-contained HTML version of the daily brief (no external assets, phone-friendly)."""

from __future__ import annotations

import math
from html import escape

from .brief import NAMES, UnderlyingScan, _pick
from .models import now_ist
from .strategies import Candidate, confidence_label

CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d1d1b;--muted:#6b6b66;--line:#e4e3de;
--up:#137a3f;--down:#b42318;--warn:#9a6700;--accent:#2f5bd3;--chip:#f0efe9}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--card:#1e1e1c;--ink:#ecebe6;--muted:#a3a29b;
--line:#33332f;--up:#4cc283;--down:#f97066;--warn:#e0b341;--accent:#8fa8ff;--chip:#2a2a27}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
main{max-width:860px;margin:0 auto;padding:20px 16px 40px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:18px;margin:28px 0 8px}h3{font-size:15px;margin:18px 0 6px}
.muted{color:var(--muted);font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:10px 0}
.hero{border-left:4px solid var(--accent)}.hero.none{border-left-color:var(--warn)}
.chip{display:inline-block;background:var(--chip);border-radius:999px;padding:1px 10px;font-size:13px;margin-right:6px}
.bullish{color:var(--up)}.bearish{color:var(--down)}.neutral{color:var(--warn)}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600}td.num{text-align:right;font-variant-numeric:tabular-nums}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:8px 0}
.kv{background:var(--chip);border-radius:8px;padding:8px 10px}.kv b{display:block;font-size:16px}
.kv span{font-size:12px;color:var(--muted)}
.note{color:var(--warn);font-size:13px}.legs{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13px}
.scroll{overflow-x:auto}footer{margin-top:30px;color:var(--muted);font-size:12px}
"""


def _rs(x: float) -> str:
    return "unlimited" if math.isinf(x) else f"₹{x:,.0f}"


def _setup_html(c: Candidate) -> str:
    lot = c.lot_size
    kind = "debit" if c.entry_value > 0 else "credit"
    legs = "<br>".join(
        f"{escape(l.side.upper())} {int(l.strike)} {escape(l.kind)} @ {l.price:.2f}" for l in c.legs
    )
    be = ", ".join(f"{b:,.0f}" for b in c.breakevens) or "n/a"
    maxp = "unlimited" if math.isinf(c.max_profit) else _rs(c.max_profit * lot)
    notes = "".join(f'<div class="note">⚠ {escape(n)}</div>' for n in c.notes)
    return f"""
<div class="card">
  <div><b>{escape(NAMES[c.strategy])}</b> · {escape(c.underlying)} · expiry {escape(c.expiry)} ({c.dte} days)</div>
  <div class="muted">id <code>{escape(c.id)}</code></div>
  <div class="legs" style="margin:8px 0">{legs}</div>
  <div class="grid">
    <div class="kv"><span>Net {kind} per lot</span><b>{_rs(abs(c.entry_value) * lot)}</b></div>
    <div class="kv"><span>Max profit per lot</span><b>{maxp}</b></div>
    <div class="kv"><span>Max loss per lot</span><b>{_rs(c.max_loss * lot)}</b></div>
    <div class="kv"><span>Breakeven</span><b>{be}</b></div>
    <div class="kv"><span>Market-implied chance of profit</span><b>{c.pop_market * 100:.0f}%</b></div>
    <div class="kv"><span>Suggested size</span><b>{c.lots} lot(s)</b></div>
  </div>
  <div><b>Exit plan:</b> take profit at +{_rs(c.target_amount * lot)}/lot, stop at −{_rs(c.stop_amount * lot)}/lot,
  close the day before expiry regardless. Charges ≈ {_rs(c.charges_per_lot)}/lot round trip.</div>
  {notes}
</div>"""


def render_html(scans: list[UnderlyingScan], cfg: dict, journal_summary: str = "") -> str:
    now = now_ist()
    acct = cfg.get("account", {})
    pick, sig = _pick(scans)
    stale = [s for s in scans if s.as_of and now.strftime("%d %b %Y") not in s.as_of]

    if pick and confidence_label(sig) != "low":
        hero = f"""
<div class="card hero">
  <div class="muted">Today's top setup</div>
  <h2 style="margin:4px 0">{escape(NAMES[pick.strategy])} on {escape(pick.underlying)}</h2>
  <span class="chip {sig.label}">{sig.label} bias {sig.bias:+.2f}</span>
  <span class="chip">signal confidence: {confidence_label(sig)}</span>
  <span class="chip">{sig.agreement * 100:.0f}% of signals agree</span>
</div>{_setup_html(pick)}"""
    elif pick:
        hero = f"""
<div class="card hero none"><h2 style="margin:4px 0">No trade today</h2>
<div>The best setup ({escape(NAMES[pick.strategy])} on {escape(pick.underlying)}) rests on a low-confidence signal
(bias {sig.bias:+.2f}). Sitting out is a valid position.</div></div>"""
    else:
        hero = """<div class="card hero none"><h2 style="margin:4px 0">No trade today</h2>
<div>Signals are neutral or mixed, and no setup passed the filters.</div></div>"""

    stale_html = ""
    if stale:
        stale_html = (
            '<div class="card note">Data is not from today ('
            + escape(", ".join(f"{s.underlying}: {s.as_of}" for s in stale))
            + "). The market may be closed. Treat these as last-close readings.</div>"
        )

    body = []
    for s in scans:
        body.append(f"<h2>{escape(s.underlying)}</h2>")
        if s.error:
            body.append(f'<div class="card note">Skipped: {escape(s.error)}</div>')
            continue
        chg = f" ({s.day_change_pct:+.2f}% on the day)" if s.day_change_pct is not None else ""
        vix = f" · India VIX {s.vix:.2f}" if s.vix else ""
        body.append(
            f'<div class="muted">Spot <b>{s.spot:,.2f}</b>{chg}{vix} · data as of {escape(s.as_of)} · lot {s.lot_size}</div>'
        )
        for e in s.expiries:
            g = e.signals
            iv = f"{g.atm_iv * 100:.1f}%" if g.atm_iv else "n/a"
            hv = f"{g.hv20 * 100:.1f}%" if g.hv20 else "n/a"
            rows = "".join(
                f"<tr><td>{escape(c.name)}</td><td class='num'>{c.score:+.2f}</td><td>{escape(c.detail)}</td></tr>"
                for c in g.components
            )
            sup = ", ".join(f"{k:,.0f}" for k, _ in g.support) or "n/a"
            res = ", ".join(f"{k:,.0f}" for k, _ in g.resistance) or "n/a"
            em = f"±{g.expected_move:,.0f}" if g.expected_move else "n/a"
            pcr = f"{g.pcr:.2f}" if g.pcr is not None else "n/a"
            body.append(f"""
<h3>Expiry {escape(e.expiry)} ({e.dte} days)</h3>
<span class="chip {g.label}">{g.label} {g.bias:+.2f}</span><span class="chip">confidence {confidence_label(g)}</span>
<span class="chip">options look {g.vol_regime}</span>
<div class="card scroll"><table><tr><th>Signal</th><th>Score</th><th>Reading</th></tr>{rows}</table>
<div class="muted" style="margin-top:8px">ATM IV {iv} vs 20-day realised {hv} · PCR {pcr} · max pain {g.max_pain:,.0f}
· expected move {em}<br>Support (put OI): {sup} · Resistance (call OI): {res}</div></div>""")
            if e.selected:
                body += [_setup_html(c) for c in e.selected[:2]]
            else:
                body.append('<div class="muted">No setup matches this signal and passes the liquidity filters.</div>')

    journal_html = f'<h2>Paper-trading scorecard</h2><div class="card">{journal_summary}</div>' if journal_summary else ""

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Market Brief {now:%d %b %Y}</title><style>{CSS}</style></head>
<body><main>
<h1>F&amp;O Market Brief · {now:%a %d %b %Y}</h1>
<div class="muted">Generated {now:%H:%M} IST from {escape(str(cfg.get('provider')))} data · paper-trading experiment ·
capital ₹{acct.get('capital', 0):,.0f} · risk {acct.get('risk_per_trade_pct')}% per trade</div>
{stale_html}{hero}{''.join(body)}{journal_html}
<footer>Research aid only, not investment advice. Bias is a weighted heuristic of trend, momentum, RSI,
put/call OI and OI walls. Chance of profit uses the option market's implied volatility. Prices assume buying at the ask
and selling at the bid. Orders are placed by you on Groww.</footer>
</main></body></html>"""
