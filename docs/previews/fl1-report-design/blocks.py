"""The evening page's text blocks: the result card, the day-by-day table, the counts with percentages and the
misses table. Every number is read from the PageView's outcomes; the page computes only differences and shares."""

from calendar_grid import month_grid
from gapchart import signed
from linechart import fmt, fmt_high, fmt_low, status

WORD = {"green": "Correct", "amber": "Close call", "red": "Missed"}
GLYPH = {"green": "✓", "amber": "⚠", "red": "✗"}


def where_it_closed(d):
    """One plain line: how far outside which range, and which way."""
    c, st = d["close"], status(d)
    if st == "green":
        side = "above" if c >= d["mid"] else "below"
        return f'Closed inside “most likely”, {fmt(abs(c - d["mid"]))} pts {side} the forecast middle'
    if st == "amber":
        gap = c - d["hi50"] if c > d["hi50"] else d["lo50"] - c
        side = "above" if c > d["hi50"] else "below"
        return f'Closed {fmt(gap)} pts {side} the most-likely range, inside “almost certainly”'
    gap = c - d["hi90"] if c > d["hi90"] else d["lo90"] - c
    side = "above" if c > d["hi90"] else "below"
    return f'Closed {fmt(gap)} pts {side} “almost certainly”'


def result_card(d):
    gap, st = d["close"] - d["mid"], status(d)
    pct = gap / d["mid"] * 100
    return (f'<div class="result"><div class="three">'
            f'<div><small>Forecast middle</small><b>{fmt(d["mid"])}</b><span>most likely {fmt_low(d["lo50"])} – '
            f'{fmt_high(d["hi50"])}</span></div>'
            f'<div><small>Actual close</small><b>{fmt(d["close"])}</b><span>{d["date_long"]}</span></div>'
            f'<div><small>Gap</small><b class="{st}">{signed(gap)} pts</b><span>'
            f'{"+" if pct >= 0 else "−"}{abs(pct):.2f}%</span></div></div>'
            f'<div class="verdict"><span class="chip {st}">{GLYPH[st]} {WORD[st]}</span>'
            f'<span class="plainline">{where_it_closed(d)}</span></div></div>')


def _reason(idx, d):
    return next((m["reason"] for m in idx["misses7"] if m["date"].split(" ", 1)[1] == d["date"]), "")


def day_table(idx, days):
    rows = []
    for d in reversed(days):
        gap, st = d["close"] - d["mid"], status(d)
        pct = gap / d["mid"] * 100
        sign = "pos" if gap >= 0 else "neg"
        reason = _reason(idx, d) if st == "red" else ""
        rows.append(f'<tr><td>{d["date"]}</td><td>{fmt(d["mid"])}</td><td>{fmt_low(d["lo50"])} – {fmt_high(d["hi50"])}</td>'
                    f'<td>{fmt_low(d["lo90"])} – {fmt_high(d["hi90"])}</td><td><b>{fmt(d["close"])}</b></td>'
                    f'<td class="{sign}">{signed(gap)}</td><td class="{sign}">{"+" if pct >= 0 else "−"}{abs(pct):.2f}%</td>'
                    f'<td class="{st}">{GLYPH[st]} {WORD[st]}</td><td class="reason">{reason}</td></tr>')
    return ('<div class="scroll"><table class="days"><thead><tr><th>Date</th><th>Forecast middle</th><th>Most likely</th>'
            '<th>Almost certainly</th><th>Actual close</th><th>Gap pts</th><th>Gap %</th><th>Result</th><th class="reason">Reason</th>'
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def counts_line(days, label):
    n = len(days)
    c = {s: sum(status(d) == s for d in days) for s in ("green", "amber", "red")}
    pct = {s: f"{c[s] / n:.0%}" if n else "–" for s in c}
    return (f'<div class="counts"><b class="green">✓ Correct {c["green"]} ({pct["green"]})</b> · '
            f'<b class="amber">⚠ Close call {c["amber"]} ({pct["amber"]})</b> · '
            f'<b class="red">✗ Missed {c["red"]} ({pct["red"]})</b> <span>of {n} {label}</span></div>')


def month_block(days, issue_day):
    this_month = [d for d in days if d["iso"][:7] == issue_day.isoformat()[:7]]
    grid = month_grid(days, issue_day)
    grid = grid[grid.index('<div class="calhead">'):]  # the grid without its own counts line
    return counts_line(this_month, f"trading days in {issue_day.strftime('%B')}") + grid


def misses_table(idx, days):
    rows = []
    for d in reversed(days):
        if status(d) != "red":
            continue
        gap = d["close"] - d["mid"]
        rows.append(f'<tr><td>{d["date"]}</td><td class="{"pos" if gap >= 0 else "neg"}">{signed(gap)}</td>'
                    f'<td>{_reason(idx, d) or "<i>reason kept for the last 7 days only (builder to extend)</i>"}</td></tr>')
    body = "".join(rows) or '<tr><td colspan="3">No miss in the last 30 days.</td></tr>'
    return ('<table class="misses"><thead><tr><th>Date</th><th>Gap pts</th><th>Reason</th></tr></thead>'
            f'<tbody>{body}</tbody></table>')
