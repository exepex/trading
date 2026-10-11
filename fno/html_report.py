"""Phone-friendly HTML market brief with inline SVG charts and plain-English explanations.

render_html(..., fragment=False) returns a full document (for the repo and PNG snapshots);
fragment=True returns the body content only (for publishing as a claude.ai Artifact page).
"""

from __future__ import annotations

import json
import math
from html import escape

from . import analytics as an
from .brief import NAMES, ExpiryScan, UnderlyingScan, _pick
from .models import now_ist
from .signals import Signals
from .strategies import Candidate, confidence_label

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800'
    '&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">'
)

CSS = """
/* Layout: a single 880px reading column; summary first (verdict, trade ticket), detail per index below. */
:root{
  --bg:#f3f6f6; --surface:#ffffff; --sunk:#e9efee; --ink:#11201f; --muted:#56635f; --line:#d6dfdd;
  --accent:#0b6e69; --accent-soft:#d5ebe8;
  --up:#13804a; --up-soft:#d7efe1; --down:#c0392f; --down-soft:#f7dcd8; --warn:#9a6a00; --warn-soft:#fbeccb;
  --s1:#2a78d6; --s2:#eb6834;
  --f-display:"Bricolage Grotesque","Avenir Next","Segoe UI",system-ui,sans-serif;
  --f-body:"IBM Plex Sans","Segoe UI",system-ui,-apple-system,sans-serif;
  --f-mono:"IBM Plex Mono",ui-monospace,"SFMono-Regular",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#0e1514; --surface:#162120; --sunk:#1d2a29; --ink:#e7efed; --muted:#9db0ac; --line:#2b3a38;
  --accent:#4dbab0; --accent-soft:#183a37;
  --up:#4cc283; --up-soft:#173628; --down:#f2776c; --down-soft:#3c1f1c; --warn:#e8b54a; --warn-soft:#3a2f14;
  --s1:#3987e5; --s2:#d95926; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#0e1514; --surface:#162120; --sunk:#1d2a29; --ink:#e7efed; --muted:#9db0ac; --line:#2b3a38;
  --accent:#4dbab0; --accent-soft:#183a37;
  --up:#4cc283; --up-soft:#173628; --down:#f2776c; --down-soft:#3c1f1c; --warn:#e8b54a; --warn-soft:#3a2f14;
  --s1:#3987e5; --s2:#d95926; color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15.5px/1.55 var(--f-body);-webkit-font-smoothing:antialiased}
.wrap{max-width:880px;margin:0 auto;padding-inline:16px;padding-block:22px 48px;display:flex;flex-direction:column;gap:22px}
h1,h2,h3{font-family:var(--f-display);text-wrap:balance;margin:0;line-height:1.15}
h1{font-size:clamp(28px,6vw,40px);font-weight:800;letter-spacing:-.02em}
h2{font-size:clamp(21px,4.4vw,26px);font-weight:800;letter-spacing:-.01em}
h3{font-size:17px;font-weight:600}
p{margin:0;max-width:68ch}
.eyebrow{font:500 12px/1 var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.muted{color:var(--muted)} .small{font-size:13.5px}
.num{font-family:var(--f-mono);font-variant-numeric:tabular-nums}
.mast{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:10px 20px;border-bottom:2px solid var(--ink);padding-bottom:14px}
.mast .meta{display:flex;flex-direction:column;gap:4px;text-align:right}
.banner{background:var(--warn-soft);color:var(--ink);border-radius:10px;padding:10px 14px;font-size:14px;display:flex;gap:10px;align-items:flex-start}
.banner b{color:var(--warn);white-space:nowrap}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px;display:flex;flex-direction:column;gap:14px;min-width:0}
.verdict{display:grid;grid-template-columns:1fr;gap:14px}
.verdict .headline{font-family:var(--f-display);font-weight:800;font-size:clamp(24px,5.2vw,34px);line-height:1.12;letter-spacing:-.015em}
.tone-bearish{color:var(--down)} .tone-bullish{color:var(--up)} .tone-neutral{color:var(--warn)}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:3px 11px;font-size:13px;background:var(--sunk);color:var(--ink);white-space:nowrap}
.chip.bearish{background:var(--down-soft);color:var(--down)} .chip.bullish{background:var(--up-soft);color:var(--up)}
.chip.neutral{background:var(--warn-soft);color:var(--warn)}
.meter{display:flex;flex-direction:column;gap:6px}
.meter .track{position:relative;height:12px;border-radius:999px;background:linear-gradient(90deg,var(--down) 0%,var(--down-soft) 38%,var(--sunk) 50%,var(--up-soft) 62%,var(--up) 100%)}
.meter .pin{position:absolute;top:50%;width:20px;height:20px;border-radius:50%;background:var(--surface);border:4px solid var(--ink);transform:translate(-50%,-50%)}
.meter .ends{display:flex;justify-content:space-between;font-size:12px;color:var(--muted)}
.why{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:6px}
.ticket{border:1.5px solid var(--ink);border-radius:14px;overflow:hidden;background:var(--surface)}
.ticket-head{display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px 14px;align-items:baseline;padding:14px 18px;background:var(--ink);color:var(--bg)}
.ticket-head h3{font-size:20px;color:var(--bg)} .ticket-head .eyebrow{color:var(--bg);opacity:.75}
.ticket-body{padding:16px 18px;display:flex;flex-direction:column;gap:16px}
.legs{display:flex;flex-direction:column;gap:6px}
.leg{display:grid;grid-template-columns:62px 1fr auto;gap:10px;align-items:center;padding:9px 12px;border-radius:10px;background:var(--sunk);font-family:var(--f-mono);font-size:14.5px}
.side{font-weight:600;font-size:12px;letter-spacing:.06em;text-align:center;border-radius:6px;padding:3px 0}
.side.buy{background:var(--up-soft);color:var(--up)} .side.sell{background:var(--down-soft);color:var(--down)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}
.kpi{background:var(--sunk);border-radius:10px;padding:10px 12px;display:flex;flex-direction:column;gap:2px;min-width:0}
.kpi span{font-size:12.5px;color:var(--muted)} .kpi b{font:600 19px/1.2 var(--f-mono);font-variant-numeric:tabular-nums}
.kpi b.up{color:var(--up)} .kpi b.down{color:var(--down)}
.plain{background:var(--accent-soft);border-radius:10px;padding:12px 14px;display:flex;flex-direction:column;gap:6px}
.plain .eyebrow{color:var(--accent)}
.rules{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px}
.rule{border:1px solid var(--line);border-radius:10px;padding:10px 12px;display:flex;flex-direction:column;gap:2px}
.rule b{font-family:var(--f-mono);font-size:16px}
.chart{width:100%;overflow-x:auto;position:relative}
.chart svg{display:block;width:100%;height:auto;min-width:340px;font-family:var(--f-body)}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px;color:var(--muted)}
.legend i{display:inline-block;width:14px;height:3px;border-radius:2px;vertical-align:middle;margin-right:6px}
.legend i.box{height:10px;width:10px;border-radius:3px}
.tip{position:absolute;pointer-events:none;background:var(--ink);color:var(--bg);font:500 12.5px/1.35 var(--f-mono);padding:6px 8px;border-radius:6px;white-space:nowrap;transform:translate(-50%,-120%)}
.sigs{display:flex;flex-direction:column;gap:2px}
.sig{display:grid;grid-template-columns:minmax(0,1fr) 120px;gap:6px 14px;align-items:center;padding:10px 0;border-bottom:1px solid var(--line)}
.sig:last-child{border-bottom:0}
.sig .t{display:flex;flex-direction:column;gap:2px;min-width:0}
.dbar{position:relative;height:10px;background:var(--sunk);border-radius:999px}
.dbar::after{content:"";position:absolute;left:50%;top:-3px;bottom:-3px;width:1.5px;background:var(--muted)}
.dbar span{position:absolute;top:0;bottom:0;border-radius:999px}
.dbar .neg{background:var(--down)} .dbar .pos{background:var(--up)}
.sig .score{font:500 12px var(--f-mono);color:var(--muted);text-align:right;margin-top:4px}
.idx-head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:4px 14px}
.alt{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 12px;padding:10px 0;border-top:1px solid var(--line);font-size:14px}
.alt code{font-family:var(--f-mono);font-size:12.5px;color:var(--muted);word-break:break-all}
.terms{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px 18px}
.term b{display:block;font-family:var(--f-display);font-size:15.5px}
.term span{font-size:14px;color:var(--muted)}
.empty{border:1.5px dashed var(--line);border-radius:10px;padding:14px;color:var(--muted);font-size:14px}
code{font-family:var(--f-mono);font-size:.92em}
footer{font-size:12.5px;color:var(--muted);border-top:1px solid var(--line);padding-top:14px;display:flex;flex-direction:column;gap:6px}
svg .grid{stroke:var(--line);stroke-width:1}
svg .axis{fill:var(--muted);font-size:11.5px}
svg .lbl{fill:var(--ink);font-size:12px;font-weight:600}
svg .lbl-m{fill:var(--muted);font-size:11.5px}
svg .lbl,svg .lbl-m{paint-order:stroke;stroke:var(--surface);stroke-width:4px;stroke-linejoin:round}
@media (max-width:520px){.mast .meta{text-align:left}.sig{grid-template-columns:1fr}.leg{grid-template-columns:54px 1fr auto}}
@media (prefers-reduced-motion:no-preference){.meter .pin{transition:left .6s ease}}
"""

SCRIPT = """
document.querySelectorAll('[data-hover]').forEach(function(box){
  var svg=box.querySelector('svg'),pts=JSON.parse(box.getAttribute('data-hover')),
      line=svg.querySelector('.xh'),tip=box.querySelector('.tip');
  if(!line||!tip)return;
  function move(e){
    var r=svg.getBoundingClientRect(),vb=svg.viewBox.baseVal,x=(e.clientX-r.left)*vb.width/r.width,best=pts[0];
    pts.forEach(function(p){if(Math.abs(p[0]-x)<Math.abs(best[0]-x))best=p});
    line.setAttribute('x1',best[0]);line.setAttribute('x2',best[0]);line.style.opacity=1;
    tip.textContent=best[2];tip.hidden=false;
    tip.style.left=(best[0]*r.width/vb.width)+'px';tip.style.top=(best[1]*r.height/vb.height)+'px';
  }
  svg.addEventListener('pointermove',move);
  svg.addEventListener('pointerleave',function(){line.style.opacity=0;tip.hidden=true});
});
"""


# ---------------------------------------------------------------- formatting


def inr(x: float, sign: bool = False) -> str:
    """Rupees with Indian digit grouping: 1,23,456."""
    if math.isinf(x):
        return "unlimited"
    neg = x < 0
    n = str(int(round(abs(x))))
    if len(n) > 3:
        head, tail = n[:-3], n[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        n = ",".join(parts + [tail])
    prefix = "−" if neg else ("+" if sign and x > 0 else "")
    return f"{prefix}₹{n}"


def pts(x: float) -> str:
    return f"{x:,.0f}"


def _nice_step(span: float, target: int = 5) -> float:
    raw = span / max(target, 1)
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


# ---------------------------------------------------------------- plain English

COMP_NAMES = {
    "trend": "Trend",
    "momentum": "Momentum, last 20 days",
    "rsi": "RSI (stretched or not)",
    "pcr": "Put/call ratio",
    "oi_range": "Floor and ceiling from option bets",
}


def explain_component(name: str, score: float, s: UnderlyingScan, sig: Signals) -> str:
    u = s.underlying
    closes = s.context.closes if s.context else []
    if name == "trend":
        if score >= 1:
            return f"{u} is above its 20-day and 50-day averages. That is an uptrend."
        if score <= -1:
            return f"{u} is below its 20-day and 50-day averages. That is a downtrend."
        return f"{u} is between its 20-day and 50-day averages, so the trend is mixed."
    if name == "momentum" and len(closes) > 21:
        ret = (closes[-1] / closes[-21] - 1) * 100
        word = "gained" if ret > 0 else "lost"
        return f"{u} has {word} {abs(ret):.1f}% over the last 20 trading days."
    if name == "rsi":
        r = an.rsi(closes) if closes else None
        if r is None:
            return "Not enough history."
        if r >= 70:
            return f"RSI is {r:.0f}: overbought. Rallies this stretched often pause."
        if r <= 30:
            return f"RSI is {r:.0f}: oversold. Falls this stretched often bounce."
        return f"RSI is {r:.0f}, in the normal zone, leaning {'strong' if r >= 50 else 'weak'}."
    if name == "pcr" and sig.pcr is not None:
        if sig.pcr >= 1:
            return f"Ratio {sig.pcr:.2f}: more puts than calls are open. Put sellers are defending a floor, mildly positive."
        return f"Ratio {sig.pcr:.2f}: more calls than puts are open. Call sellers are capping the upside, mildly negative."
    if name == "oi_range" and sig.support and sig.resistance:
        floor, ceil = sig.support[0][0], sig.resistance[0][0]
        nearer = "ceiling" if score < 0 else "floor"
        return (
            f"Biggest put bets sit at {pts(floor)} (a floor) and call bets at {pts(ceil)} (a ceiling). "
            f"{u} is nearer the {nearer}."
        )
    return ""


def headline(sig: Signals, u: str, has_trade: bool) -> str:
    if not has_trade:
        return "No trade today. Signals are mixed, so sitting out is the plan."
    if sig.label == "bearish":
        return f"{u} looks weak. Today's idea gains if {u} falls."
    if sig.label == "bullish":
        return f"{u} looks strong. Today's idea gains if {u} rises."
    return f"{u} looks range-bound. Today's idea gains if {u} stays put."


def trade_in_words(c: Candidate) -> list[str]:
    u, lot = c.underlying, c.lot_size
    strikes = sorted(l.strike for l in c.legs)
    be = c.breakevens
    exp = c.expiry
    best, worst = inr(c.max_profit * lot, True), inr(-c.max_loss * lot)
    if c.strategy == "bear_put_spread":
        return [
            f"You make money if {u} is below {pts(be[0])} on expiry day ({exp}).",
            f"Best case: {u} at or below {pts(strikes[0])} gives {best} per lot.",
            f"Worst case: {u} at or above {pts(strikes[-1])} gives {worst} per lot. You can never lose more than that.",
        ]
    if c.strategy == "bull_call_spread":
        return [
            f"You make money if {u} is above {pts(be[0])} on expiry day ({exp}).",
            f"Best case: {u} at or above {pts(strikes[-1])} gives {best} per lot.",
            f"Worst case: {u} at or below {pts(strikes[0])} gives {worst} per lot. You can never lose more than that.",
        ]
    if c.strategy == "long_put":
        return [
            f"You make money if {u} is below {pts(be[0])} on expiry day ({exp}). The further it falls, the more you make.",
            f"Worst case: {u} at or above {pts(strikes[0])} gives {worst} per lot.",
        ]
    if c.strategy == "long_call":
        return [
            f"You make money if {u} is above {pts(be[0])} on expiry day ({exp}). The further it rises, the more you make.",
            f"Worst case: {u} at or below {pts(strikes[0])} gives {worst} per lot.",
        ]
    lo, hi = (be + [0, 0])[:2]
    return [
        f"You make money if {u} stays between {pts(lo)} and {pts(hi)} until expiry ({exp}).",
        f"Best case {best} per lot; worst case {worst} per lot.",
    ]


# ---------------------------------------------------------------- charts


def price_chart(s: UnderlyingScan, n: int = 120) -> str:
    ctx = s.context
    if not ctx or len(ctx.closes) < 60:
        return ""
    closes = ctx.closes
    e20, e50 = an.ema(closes, 20), an.ema(closes, 50)
    closes, e20, e50 = closes[-n:], e20[-n:], e50[-n:]
    dates = ctx.dates[-n:] if len(ctx.dates) >= n else []
    W, H, L, R, T, B = 680, 250, 54, 72, 14, 30
    lo, hi = min(closes + e20 + e50), max(closes + e20 + e50)
    step = _nice_step(hi - lo, 5)
    y0, y1 = math.floor(lo / step) * step, math.ceil(hi / step) * step

    def X(i):
        return L + (W - L - R) * i / (len(closes) - 1)

    def Y(v):
        return T + (H - T - B) * (1 - (v - y0) / (y1 - y0))

    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{escape(s.underlying)} price over the last {n} sessions">']
    v = y0
    while v <= y1 + 1e-9:
        out.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>')
        out.append(f'<text class="axis" x="{L - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{v:,.0f}</text>')
        v += step
    if dates:
        last_m = None
        for i, d in enumerate(dates):
            if d.month != last_m and i > 3:
                out.append(f'<line class="grid" x1="{X(i):.1f}" x2="{X(i):.1f}" y1="{H - B}" y2="{H - B + 4}"/>')
                out.append(f'<text class="axis" x="{X(i):.1f}" y="{H - 10}" text-anchor="middle">{d:%b}</text>')
            last_m = d.month

    def path(vals):
        return "M" + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))

    area = path(closes) + f" L{X(len(closes) - 1):.1f},{H - B} L{L},{H - B} Z"
    out.append(f'<path d="{area}" fill="var(--accent)" fill-opacity=".08" stroke="none"/>')
    out.append(f'<path d="{path(e50)}" fill="none" stroke="var(--s2)" stroke-width="2"/>')
    out.append(f'<path d="{path(e20)}" fill="none" stroke="var(--s1)" stroke-width="2"/>')
    out.append(f'<path d="{path(closes)}" fill="none" stroke="var(--ink)" stroke-width="2.2"/>')
    # end labels, nudged apart so they never overlap
    ends = sorted(
        [(Y(closes[-1]), f"{closes[-1]:,.0f}", "var(--ink)"), (Y(e20[-1]), "EMA 20", "var(--muted)"),
         (Y(e50[-1]), "EMA 50", "var(--muted)")]
    )
    for i in range(1, len(ends)):
        if ends[i][0] - ends[i - 1][0] < 14:
            ends[i] = (ends[i - 1][0] + 14, ends[i][1], ends[i][2])
    for y, text, color in ends:
        out.append(f'<text x="{W - R + 8}" y="{y + 4:.1f}" font-size="12" font-weight="600" fill="{color}">{text}</text>')
    xe, ye = X(len(closes) - 1), Y(closes[-1])
    out.append(f'<circle cx="{xe:.1f}" cy="{ye:.1f}" r="4.5" fill="var(--ink)" stroke="var(--surface)" stroke-width="2"/>')
    out.append(f'<line class="xh" x1="0" x2="0" y1="{T}" y2="{H - B}" stroke="var(--muted)" stroke-dasharray="3 3" style="opacity:0"/>')
    out.append("</svg>")
    hover = [
        [round(X(i), 1), round(Y(c), 1), f"{dates[i]:%d %b}: {c:,.0f}" if dates else f"{c:,.0f}"]
        for i, c in enumerate(closes)
    ]
    legend = (
        '<div class="legend"><span><i style="background:var(--ink)"></i>Close</span>'
        '<span><i style="background:var(--s1)"></i>20-day average</span>'
        '<span><i style="background:var(--s2)"></i>50-day average</span></div>'
    )
    return (
        f"<div class=\"chart\" data-hover='{escape(json.dumps(hover))}'>{''.join(out)}<div class=\"tip\" hidden></div></div>{legend}"
    )


def oi_chart(e: ExpiryScan, spot: float) -> str:
    rows = e.oi_profile
    if not rows:
        return ""
    W, rh, top = 680, 22, 26
    mid_w, margin = 76, 62
    half = (W - mid_w - 2 * margin) / 2
    cx_l, cx_r = margin + half, margin + half + mid_w
    mx = max(max(c, p) for _, c, p in rows) or 1
    H = top + rh * len(rows) + 8
    sup = {k for k, _ in e.signals.support[:1]}
    res = {k for k, _ in e.signals.resistance[:1]}
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Open interest by strike, puts left, calls right">']
    out.append(f'<text class="lbl-m" x="{cx_l - 4}" y="14" text-anchor="end">◀ Put bets (floor)</text>')
    out.append(f'<text class="lbl-m" x="{cx_r + 4}" y="14">Call bets (ceiling) ▶</text>')
    for i, (k, c, p) in enumerate(rows):
        y = top + i * rh
        wp, wc = (half - 8) * p / mx, (half - 8) * c / mx
        out.append(
            f'<rect x="{cx_l - wp:.1f}" y="{y + 3}" width="{max(wp, 1):.1f}" height="{rh - 6}" rx="3" fill="var(--s2)">'
            f"<title>{pts(k)} put OI: {p:,.0f}</title></rect>"
        )
        out.append(
            f'<rect x="{cx_r:.1f}" y="{y + 3}" width="{max(wc, 1):.1f}" height="{rh - 6}" rx="3" fill="var(--s1)">'
            f"<title>{pts(k)} call OI: {c:,.0f}</title></rect>"
        )
        cls = "lbl" if k in sup or k in res else "axis"
        out.append(f'<text class="{cls}" x="{W / 2:.1f}" y="{y + rh / 2 + 4:.1f}" text-anchor="middle">{pts(k)}</text>')
        if k in sup:
            out.append(f'<text class="lbl" x="{cx_l - wp - 6:.1f}" y="{y + rh / 2 + 4:.1f}" text-anchor="end">floor</text>')
        if k in res:
            out.append(f'<text class="lbl" x="{cx_r + wc + 6:.1f}" y="{y + rh / 2 + 4:.1f}">ceiling</text>')
    strikes = [k for k, _, _ in rows]
    if strikes[0] <= spot <= strikes[-1]:
        j = max(i for i, k in enumerate(strikes) if k <= spot)
        frac = 0 if j == len(strikes) - 1 else (spot - strikes[j]) / (strikes[j + 1] - strikes[j])
        ys = top + (j + frac) * rh + rh / 2
        out.append(f'<line x1="50" x2="{W - 4}" y1="{ys:.1f}" y2="{ys:.1f}" stroke="var(--ink)" stroke-width="1.5" stroke-dasharray="5 4"/>')
        out.append(
            f'<rect x="4" y="{ys - 10:.1f}" width="46" height="20" rx="10" fill="var(--ink)"/>'
            f'<text x="27" y="{ys + 4:.1f}" text-anchor="middle" font-size="11.5" font-weight="600" fill="var(--bg)">spot</text>'
        )
    out.append("</svg>")
    legend = (
        '<div class="legend"><span><i class="box" style="background:var(--s2)"></i>Put open interest</span>'
        '<span><i class="box" style="background:var(--s1)"></i>Call open interest</span>'
        f'<span><i style="background:var(--ink)"></i>Dashed line: spot {pts(spot)}</span></div>'
    )
    return f'<div class="chart">{"".join(out)}</div>{legend}'


def payoff_chart(c: Candidate, em: float | None) -> str:
    lot = c.lot_size
    strikes = [l.strike for l in c.legs]
    span = max((em or c.spot * 0.02) * 2.4, (max(strikes) - min(strikes)) * 1.6, c.spot * 0.02)
    x0, x1 = min(c.spot - span, min(strikes) - span * 0.3), max(c.spot + span, max(strikes) + span * 0.3)
    N = 160
    xs = [x0 + (x1 - x0) * i / N for i in range(N + 1)]
    ys = [c.payoff(x) * lot for x in xs]
    lo, hi = min(ys + [0]), max(ys + [0])
    pad = (hi - lo) * 0.12 or 1
    lo, hi = lo - pad, hi + pad
    W, H, L, R, T, B = 680, 260, 70, 16, 16, 34

    def X(v):
        return L + (W - L - R) * (v - x0) / (x1 - x0)

    def Y(v):
        return T + (H - T - B) * (1 - (v - lo) / (hi - lo))

    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Profit or loss per lot at expiry">']
    if em:
        a, b = X(max(c.spot - em, x0)), X(min(c.spot + em, x1))
        out.append(f'<rect x="{a:.1f}" y="{T}" width="{b - a:.1f}" height="{H - T - B}" fill="var(--accent)" fill-opacity=".09"/>')
        out.append(f'<text class="lbl-m" x="{(a + b) / 2:.1f}" y="{T + 13}" text-anchor="middle">likely range by expiry (±{pts(em)})</text>')
    out.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke-width="1.5"/>')
    for v, lab in ((max(ys), inr(max(ys), True)), (min(ys), inr(min(ys)))):
        if not math.isinf(v):
            out.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke-dasharray="2 4"/>')
            out.append(f'<text class="axis" x="{L - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{lab}</text>')
    out.append(f'<text class="axis" x="{L - 8}" y="{Y(0) + 4:.1f}" text-anchor="end">₹0</text>')
    pos = "M" + " L".join(f"{X(x):.1f},{Y(max(y, 0)):.1f}" for x, y in zip(xs, ys)) + f" L{X(x1):.1f},{Y(0):.1f} L{X(x0):.1f},{Y(0):.1f} Z"
    neg = "M" + " L".join(f"{X(x):.1f},{Y(min(y, 0)):.1f}" for x, y in zip(xs, ys)) + f" L{X(x1):.1f},{Y(0):.1f} L{X(x0):.1f},{Y(0):.1f} Z"
    out.append(f'<path d="{pos}" fill="var(--up)" fill-opacity=".22" stroke="none"/>')
    out.append(f'<path d="{neg}" fill="var(--down)" fill-opacity=".2" stroke="none"/>')
    line = "M" + " L".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in zip(xs, ys))
    out.append(f'<path d="{line}" fill="none" stroke="var(--ink)" stroke-width="2.2"/>')
    step = _nice_step(x1 - x0, 5)
    v = math.ceil(x0 / step) * step
    while v <= x1:
        out.append(f'<text class="axis" x="{X(v):.1f}" y="{H - 12}" text-anchor="middle">{v:,.0f}</text>')
        v += step
    xs_ = X(c.spot)
    out.append(f'<line x1="{xs_:.1f}" x2="{xs_:.1f}" y1="{T + 20}" y2="{H - B}" stroke="var(--ink)" stroke-width="1.5"/>')
    out.append(f'<text class="lbl" x="{xs_ + 5:.1f}" y="{T + 32}">today {pts(c.spot)}</text>')
    for be in c.breakevens:
        xb = X(be)
        out.append(f'<line x1="{xb:.1f}" x2="{xb:.1f}" y1="{Y(0) - 26:.1f}" y2="{Y(0) + 26:.1f}" stroke="var(--muted)" stroke-dasharray="3 3"/>')
        out.append(f'<circle cx="{xb:.1f}" cy="{Y(0):.1f}" r="4.5" fill="var(--surface)" stroke="var(--ink)" stroke-width="2"/>')
        out.append(f'<text class="lbl-m" x="{xb:.1f}" y="{Y(0) - 32:.1f}" text-anchor="middle">breakeven {pts(be)}</text>')
    out.append(f'<line class="xh" x1="0" x2="0" y1="{T}" y2="{H - B}" stroke="var(--muted)" stroke-dasharray="3 3" style="opacity:0"/>')
    out.append("</svg>")
    hover = [[round(X(x), 1), round(Y(y), 1), f"{c.underlying} at {x:,.0f}: {inr(y, True)}"] for x, y in zip(xs, ys)]
    return f"<div class=\"chart\" data-hover='{escape(json.dumps(hover))}'>{''.join(out)}<div class=\"tip\" hidden></div></div>"


# ---------------------------------------------------------------- sections


def meter(sig: Signals) -> str:
    left = (sig.bias + 1) / 2 * 100
    return (
        f'<div class="meter" aria-label="Direction score {sig.bias:+.2f} on a scale from -1 to +1">'
        f'<div class="track"><div class="pin" style="left:{left:.1f}%"></div></div>'
        '<div class="ends"><span>Bearish −1</span><span>Neutral 0</span><span>Bullish +1</span></div></div>'
    )


def ticket(c: Candidate, sig: Signals, em: float | None, capital: float) -> str:
    lot = c.lot_size
    legs = "".join(
        f'<div class="leg"><span class="side {l.side}">{l.side.upper()}</span>'
        f"<span>{escape(name)}</span>"
        f'<span class="num">₹{l.price:.2f}</span></div>'
        for l, name in zip(c.legs, c.contract_names())
    )
    kind = "Cost per lot" if c.entry_value > 0 else "Credit per lot"
    be = ", ".join(pts(b) for b in c.breakevens) or "n/a"
    notes = "".join(f'<div class="banner"><b>Note</b><span>{escape(n)}</span></div>' for n in c.notes)
    words = "".join(f"<p>{escape(w)}</p>" for w in trade_in_words(c))
    return f"""
<section class="ticket" aria-label="Suggested trade">
  <div class="ticket-head"><div><div class="eyebrow">Suggested trade · paper only</div>
  <h3>{escape(NAMES[c.strategy])} · {escape(c.underlying)}</h3></div>
  <div class="eyebrow">expiry {escape(c.expiry)} · {c.dte} days · lot {lot}</div></div>
  <div class="ticket-body">
    <div class="legs">{legs}</div>
    <p class="muted small">Type the name exactly as shown into Groww search to find the contract.</p>
    <div class="kpis">
      <div class="kpi"><span>{kind}</span><b>{inr(abs(c.entry_value) * lot)}</b></div>
      <div class="kpi"><span>Most you can lose</span><b class="down">{inr(-c.max_loss * lot)}</b></div>
      <div class="kpi"><span>Most you can make</span><b class="up">{inr(c.max_profit * lot, True) if c.strategy not in ("long_put", "long_call") else "no cap"}</b></div>
      <div class="kpi"><span>Breakeven at expiry</span><b>{be}</b></div>
      <div class="kpi"><span>Chance of profit*</span><b>{c.pop_market * 100:.0f}%</b></div>
      <div class="kpi"><span>Suggested size · money used</span><b>{c.lots} lot{'s' if c.lots != 1 else ''} · {inr(c.capital_used)}</b></div>
    </div>
    <div class="plain"><div class="eyebrow">In plain words</div>{words}</div>
    <div><h3>Profit or loss at expiry, per lot</h3><p class="muted small">Green is profit, red is loss. Hover or tap the chart to read a value.</p></div>
    {payoff_chart(c, em)}
    <div><h3>Exit plan</h3></div>
    <div class="rules">
      <div class="rule"><span class="muted small">Take profit when the trade is up</span><b class="up">{inr(c.target_amount * lot, True)}</b></div>
      <div class="rule"><span class="muted small">Cut the loss when the trade is down</span><b class="down">{inr(-c.stop_amount * lot)}</b></div>
      <div class="rule"><span class="muted small">Close it anyway</span><b>1 day before expiry</b></div>
    </div>
    <p class="muted small">Charges ≈ {inr(c.charges_per_lot)} per lot for entry and exit. Planned loss at the stop
    ≈ {inr(c.stop_amount * c.lot_size * max(c.lots, 1))}; if held to expiry the most you can lose is
    {inr(c.max_loss * c.lot_size * max(c.lots, 1))}. *Chance of profit is what option prices themselves imply,
    not a promise. Paper-trade id <code>{escape(c.id)}</code>.</p>
    {notes}
  </div>
</section>"""


def index_section(s: UnderlyingScan) -> str:
    if s.error:
        return f'<section class="panel"><h2>{escape(s.underlying)}</h2><div class="empty">Skipped: {escape(s.error)}</div></section>'
    e = s.expiries[0]
    sig = e.signals
    chg = s.day_change_pct
    chg_html = f'<b class="{"up" if (chg or 0) >= 0 else "down"}">{chg:+.2f}%</b>' if chg is not None else "<b>n/a</b>"
    em = f"±{pts(sig.expected_move)}" if sig.expected_move else "n/a"
    iv = f"{sig.atm_iv * 100:.1f}%" if sig.atm_iv else "n/a"
    sigs = []
    for c in sig.components:
        w = abs(c.score) * 50
        bar = f'<span class="{"pos" if c.score >= 0 else "neg"}" style="{"left" if c.score >= 0 else "right"}:50%;width:{w:.1f}%"></span>'
        sigs.append(
            f'<div class="sig"><div class="t"><b>{escape(COMP_NAMES.get(c.name, c.name))}</b>'
            f'<span class="small muted">{escape(explain_component(c.name, c.score, s, sig))}</span></div>'
            f'<div><div class="dbar" aria-label="score {c.score:+.2f}">{bar}</div><div class="score">{c.score:+.2f}</div></div></div>'
        )
    vol_words = {
        "cheap": "Options are priced cheaply compared with recent moves, which favours buying them.",
        "normal": "Options are fairly priced compared with recent moves.",
        "rich": "Options are expensive compared with recent moves, so buying plain calls or puts is avoided.",
    }[sig.vol_regime]
    alts = []
    for ex in s.expiries:
        for c in ex.selected[:2]:
            alts.append(
                f'<div class="alt"><div><b>{escape(NAMES[c.strategy])}</b> · {ex.expiry} · '
                + " / ".join(f"{l.side[0].upper()} {pts(l.strike)}{l.kind}" for l in c.legs)
                + f'<br><code>{escape(c.id)}</code></div><div class="num" style="text-align:right">'
                f"risk {inr(c.max_loss * c.lot_size)}<br><span class=\"muted\">{c.pop_market * 100:.0f}% chance</span></div></div>"
            )
    alts_html = (
        '<div><h3>Other setups that fit</h3>' + "".join(alts) + "</div>" if alts else
        '<div class="empty">No setup fits this signal and passes the liquidity checks.</div>'
    )
    return f"""
<section class="panel" aria-label="{escape(s.underlying)}">
  <div class="idx-head"><h2>{escape(s.underlying)}</h2>
    <div class="chips"><span class="chip {sig.label}">{sig.label} {sig.bias:+.2f}</span>
    <span class="chip">confidence {confidence_label(sig)}</span></div></div>
  <div class="kpis">
    <div class="kpi"><span>Spot</span><b>{s.spot:,.2f}</b></div>
    <div class="kpi"><span>Day change</span>{chg_html}</div>
    <div class="kpi"><span>Expected move by {e.expiry[5:]}</span><b>{em}</b></div>
    <div class="kpi"><span>India VIX · ATM IV</span><b>{f"{s.vix:.1f}" if s.vix else "n/a"} · {iv}</b></div>
  </div>
  <div><h3>Price, last 6 months</h3></div>
  {price_chart(s)}
  <div><h3>Where traders placed their option bets</h3>
  <p class="muted small">Open interest for the {e.expiry} expiry. Big put piles often act as a floor, big call piles as a ceiling.
  Max pain {pts(sig.max_pain)}. Put/call ratio {sig.pcr:.2f}.</p></div>
  {oi_chart(e, s.spot)}
  <div><h3>What the signals say</h3><p class="muted small">{escape(vol_words)}</p></div>
  <div class="sigs">{''.join(sigs)}</div>
  {alts_html}
</section>"""


TERMS = [
    ("Call option", "Gains when the index rises. You pay a premium for it."),
    ("Put option", "Gains when the index falls. You pay a premium for it."),
    ("Strike", "The index level the option is based on, such as 22,500."),
    ("Expiry", "The date the option ends. NSE index options expire on Tuesdays."),
    ("Lot", "The fixed unit you trade in. One NIFTY lot is 65 units."),
    ("Spread", "Buying one option and selling another to cut the cost and cap the risk."),
    ("Open interest (OI)", "How many contracts are still open at a strike. Big piles show where traders expect a floor or ceiling."),
    ("Put/call ratio", "Open puts divided by open calls. Above 1 leans positive, below 1 leans negative."),
    ("Implied volatility", "How big a move option prices expect. High IV means options are expensive."),
    ("Max pain", "The level where option buyers as a group would lose the most at expiry."),
    ("Stop loss", "The loss at which you exit, no matter what, so one bad trade stays small."),
    ("Paper trade", "A practice trade tracked as if real, with no money at risk."),
]


def scorecard(stats: dict | None, log: list[str]) -> str:
    if not stats or (stats["closed"] == 0 and stats["open"] == 0):
        return (
            '<div class="empty">No paper trades yet. To log today\'s idea, tell Claude "log today\'s trade", '
            'or run <code>python -m fno paper open &lt;id&gt;</code>. Results build up here every day.</div>'
        )
    net = stats["net"]
    tiles = f"""<div class="kpis">
      <div class="kpi"><span>Closed trades</span><b>{stats['closed']}</b></div>
      <div class="kpi"><span>Win rate</span><b>{stats['win_rate']:.0f}%</b></div>
      <div class="kpi"><span>Net P&amp;L after charges</span><b class="{'up' if net >= 0 else 'down'}">{inr(net, True)}</b></div>
      <div class="kpi"><span>Open now · unrealised</span><b>{stats['open']} · {inr(stats['unrealised'], True)}</b></div></div>"""
    lines = "".join(f'<p class="small muted">{escape(x)}</p>' for x in log)
    return tiles + lines


def render_html(
    scans: list[UnderlyingScan],
    cfg: dict,
    journal_stats: dict | None = None,
    journal_log: list[str] | None = None,
    fragment: bool = False,
) -> str:
    now = now_ist()
    acct = cfg.get("account", {})
    capital = acct.get("capital", 1)
    pick, sig = _pick(scans)
    trade_on = bool(pick and confidence_label(sig) != "low")
    lead = next((s for s in scans if s.expiries), None)
    lead_sig = sig if pick else (lead.expiries[0].signals if lead else None)
    lead_u = pick.underlying if pick else (lead.underlying if lead else "Market")
    stale = [s for s in scans if s.as_of and now.strftime("%d %b %Y") not in s.as_of]
    as_of = next((s.as_of for s in scans if s.as_of), "n/a")

    stale_html = ""
    if stale:
        stale_html = (
            f'<div class="banner"><b>Heads up</b><span>Prices are from {escape(as_of)}, not today. '
            "The market may be closed. Read this as a last-close view.</span></div>"
        )

    why = []
    if lead_sig and lead:
        scan_for = next((s for s in scans if s.underlying == lead_u), lead)
        for comp in sorted(lead_sig.components, key=lambda c: -abs(c.score * c.weight))[:3]:
            text = explain_component(comp.name, comp.score, scan_for, lead_sig)
            if text:
                why.append(f"<li>{escape(text)}</li>")
    verdict = ""
    if lead_sig:
        verdict = f"""
<section class="panel verdict" aria-label="Today's call">
  <div class="eyebrow">Today's call</div>
  <div class="headline tone-{lead_sig.label if trade_on else 'neutral'}">{escape(headline(lead_sig, lead_u, trade_on))}</div>
  <div class="chips"><span class="chip {lead_sig.label}">{lead_sig.label}</span>
  <span class="chip">confidence {confidence_label(lead_sig)}</span>
  <span class="chip">{lead_sig.agreement * 100:.0f}% of signals agree</span></div>
  {meter(lead_sig)}
  <div><div class="eyebrow" style="margin-bottom:6px">Why</div><ul class="why">{''.join(why)}</ul></div>
</section>"""

    em = None
    if pick:
        for s in scans:
            for e in s.expiries:
                if e.expiry == pick.expiry and s.underlying == pick.underlying:
                    em = e.signals.expected_move
    ticket_html = ticket(pick, sig, em, capital) if trade_on else ""

    terms = "".join(f'<div class="term"><b>{escape(t)}</b><span>{escape(d)}</span></div>' for t, d in TERMS)
    body = f"""
<div class="wrap">
  <header class="mast">
    <div><div class="eyebrow">F&amp;O desk · NSE index options</div><h1>Market Brief</h1></div>
    <div class="meta"><b>{now:%A, %d %B %Y}</b>
    <span class="muted small">Prices as of {escape(as_of)} · {escape(str(cfg.get('provider')).upper())} data</span>
    <span class="muted small">Paper capital {inr(capital)} · {inr(cfg.get('position_rules', {}).get('per_trade_budget', 0))} per trade · max {acct.get('max_open_trades')} open</span></div>
  </header>
  {stale_html}
  {verdict}
  {ticket_html}
  {''.join(index_section(s) for s in scans)}
  <section class="panel" aria-label="Paper-trading scorecard"><h2>Paper-trading scorecard</h2>{scorecard(journal_stats, journal_log or [])}</section>
  <section class="panel" aria-label="Jargon buster"><h2>Jargon buster</h2><div class="terms">{terms}</div></section>
  <footer><span>Research aid for a paper-trading experiment, not investment advice. Direction comes from a weighted
  mix of trend, momentum, RSI, put/call ratio and open-interest levels; it can be wrong. Prices assume buying at the ask
  and selling at the bid. You place any real order yourself on Groww.</span>
  <span>Generated {now:%d %b %Y, %H:%M} IST.</span></footer>
</div>"""
    title = f"<title>Market Brief {now:%d %b %Y}</title>"
    if fragment:
        return f"<title>F&amp;O Market Brief</title>\n{FONTS}\n<style>{CSS}</style>\n{body}\n<script>{SCRIPT}</script>\n"
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        f"{title}{FONTS}<style>{CSS}</style></head><body>{body}<script>{SCRIPT}</script></body></html>\n"
    )
