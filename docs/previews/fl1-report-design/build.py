"""Builds the v6 preview pages from the builder's PageView dump (pageview-<day>.json): `python build.py` writes
fl1-report-picture.html (the overview strip and one line chart per index) and fl1-report-details.html (everything).
Standard library only; the pages draw the PageView's values and never compute a forecast number."""

import json
from pathlib import Path

from linechart import ForecastLineChart, Layout, fmt, fmt_high, fmt_low, status

HERE = Path(__file__).parent
PICTURE_DAYS = 8
GRID_STEP = {"NIFTY": 100, "BANKNIFTY": 250}
WORD = {"green": "Correct", "amber": "Close call", "red": "Missed"}
GLYPH = {"green": "✓", "amber": "⚠", "red": "✗"}
MEANS = {"green": "inside “most likely”", "amber": "inside “almost certainly” only", "red": "outside both"}


def _head(title, body_class=""):
    css = (HERE / "report.css").read_text()
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>'
            f'<style>{css}</style></head><body class="{body_class}"><div class="wrap">')


def _header(data):
    return (f'<header><h1>Forecast report <span>{data["report_day"]} · {data["report_time"]}</span></h1>'
            f'<span class="tag">{data["preview_note"]}</span></header>')


def _range(f, key="50"):
    return f'{fmt_low(f["lo" + key])} – {fmt_high(f["hi" + key])}'


def _light(idx):
    if idx["light"] == "none":
        return f'<span class="light none"><i></i>{idx["light_word"]}</span>'
    return f'<span class="light {idx["light"]}"><i></i>{idx["light_word"]}: {idx["right30"]} of {idx["scored"]} days</span>'


def _chip(st):
    return f'<span class="chip {st}">{GLYPH[st]} {WORD[st]}</span>'


def _reason(idx, day):
    for m in idx["misses7"]:
        if m["date"].split(" ", 1)[1] == day["date"]:
            return f'<div class="why1">Why: {m["reason"]}.</div>'
    return ""


def _overview_row(idx):
    today = idx["days"][-1]  # the last scored session: today's once the builder adds today's close to the timeline
    st = status(today)
    return (f'<div class="ov"><div class="ov-head"><b>{idx["name"]}</b>{_light(idx)}</div>'
            f'<div class="ov-line"><span class="k">Call for {today["date"]}</span>'
            f'<span>{_range(today)} · closed <b>{fmt(today["close"])}</b></span>{_chip(st)}</div>'
            f'<div class="ov-sub">{MEANS[st]} ({_range(today, "90")})</div>'
            f'{_reason(idx, today) if st == "red" else ""}'
            f'<div class="ov-line"><span class="k">Next</span><span><b>{idx["next"]["date"]}</b>: most likely '
            f'<b class="big">{_range(idx["next"])}</b> · almost certainly {_range(idx["next"], "90")}</span></div></div>')


def _overview(data):
    return ('<div class="card glance"><div class="h first">At a glance</div>'
            + "".join(_overview_row(idx) for idx in data["indices"]) + "</div>")


def _chart(idx, days, width):
    chart = ForecastLineChart(days, idx["next"], Layout(width=width, grid_step=GRID_STEP[idx["name"]]))
    return chart.svg(f'{idx["name"]}: forecast high and low, the close, and the next-day forecast')


def _key():
    return ('<p class="key"><span><i class="ln hi"></i>forecast high</span><span><i class="ln lo"></i>forecast low</span>'
            '<span><i class="ln close"></i>actual close</span><span><i class="dot green"></i>✓ inside “most likely”</span>'
            '<span><i class="dot amber"></i>⚠ inside “almost certainly” only</span>'
            '<span><i class="dot red"></i>✗ outside both</span></p>')


def _tally(idx, days):
    days = days[-idx["scored"]:] if idx["scored"] else days
    counts = {s: sum(status(d) == s for d in days) for s in ("green", "amber", "red")}
    red_dates = f' ({", ".join(idx["wrong_days"])})' if idx["wrong_days"] else ""
    return (f'<p class="tally">Last {len(days)} days: <b class="green">{counts["green"]} ✓ correct</b> · '
            f'<b class="amber">{counts["amber"]} ⚠ close call</b> · <b class="red">{counts["red"]} ✗ missed</b>'
            f'{red_dates}.</p>')


def chart_card(idx, days, width):
    grid = GRID_STEP[idx["name"]]
    return (f'<div class="card"><div class="top"><h2>{idx["name"]}</h2><span class="sub">closed today at '
            f'{fmt(idx["today"])} · gridlines every {grid} points</span></div>'
            f'<div class="scroll">{_chart(idx, days, width)}</div>{_key()}{_tally(idx, idx["days"])}</div>')


def _foot(data):
    if data["system"]:
        system = "".join(f'<span class="bad">⚠ {line}</span>' for line in data["system"])
    else:
        system = f'<span class="ok">✓ {data["system_line"]}</span>'
    return f'<div class="foot">{system}<span class="research">{data["research_line"]}</span></div>'


def picture(data):
    cards = "".join(chart_card(idx, idx["days"][-PICTURE_DAYS:], 568) for idx in data["indices"])
    return (_head(f'Forecast, {data["report_day"]}') + _header(data) + _overview(data) + cards + _foot(data)
            + "</div></body></html>")


def _three(idx):
    t = idx["three"]
    return (f'<div class="h">In 3 trading days · {t["date"]}</div><p class="plain big">most likely '
            f'<b>{_range(t)}</b> · almost certainly {_range(t, "90")} · middle {fmt(t["mid"])}</p>')


def _why_missed(idx):
    items = idx["misses7"]
    body = "".join(
        f'<li><b>{m["date"]}</b>: closed {m["points"]} points {m["side"]} “almost certainly”. '
        f'<span>Likely reason, after the fact: {m["reason"]}.</span></li>' for m in items) or \
        "<li>No misses in the last 7 trading days.</li>"
    return f'<div class="h">Why it missed · last 7 trading days</div><ul class="why">{body}</ul>'


def _days_table(idx):
    rows = []
    for d in reversed(idx["days"][-30:]):
        st = status(d)
        live = ' <span class="live">live</span>' if d["live"] else ""
        rows.append(f'<tr><td>{d["date"]}{live}</td><td>{fmt(d["lo50"])} – {fmt(d["hi50"])}</td>'
                    f'<td>{fmt(d["lo90"])} – {fmt(d["hi90"])}</td><td>{fmt(d["mid"])}</td><td><b>{fmt(d["close"])}</b></td>'
                    f'<td class="{st}">{GLYPH[st]} {WORD[st]}</td></tr>')
    return ('<div class="h">Last 30 days in numbers · each forecast made the session before · '
            '<span class="live">live</span> = a sealed live forecast, the rest back-fill history</div><div class="scroll">'
            '<table class="days"><thead><tr><th>Day</th><th>Most likely</th><th>Almost certainly</th>'
            '<th>Middle</th><th>Closed</th><th>Result</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>")


def _methods(idx, horizon):
    block = idx["methods"][horizon]
    dates = [d["date"] for d in idx["days"][-len(next(iter(block["grid"].values()))):]]
    glyph = {"in50": "✓", "in90": "✓", "miss": "✗", "none": "·"}
    head = "".join(f"<th>{d.split()[0]}</th>" for d in dates)
    best = {s["method"] for s in block["scores"] if s["best"]}
    grid = "".join(f'<tr><th class="m">{m}{" ★" if m in best else ""}</th>'
                   + "".join(f'<td class="{c}">{glyph[c]}</td>' for c in cells) + "</tr>"
                   for m, cells in block["grid"].items())
    scores = "".join(f'<tr><td>{s["method"]}{" ★" if s["best"] else ""}</td><td>{s["in50"]}</td>'
                     f'<td>{s["in90"]}</td><td>{s["err"]}</td></tr>' for s in block["scores"])
    months = f'{dates[0].split()[1]} → {dates[-1].split()[1]}'
    return (f'<details class="more"><summary>Every method, {horizon} (for the curious)</summary><div class="inner">'
            f'<div class="scroll"><table class="hits"><thead><tr><th class="m">{months}</th>{head}</tr></thead>'
            f'<tbody>{grid}</tbody></table></div>'
            '<p class="plain">Bright ✓ inside the 50% range, pale ✓ inside the 90% range only, ✗ outside both. '
            '★ = the method shown in the report: best on history, not yet proven live.</p>'
            '<div class="scroll"><table class="scores"><thead><tr><th>Method</th>'
            '<th>In 50% range<br>7 · 14 · 30 days</th><th>In 90% range<br>7 · 14 · 30 days</th>'
            f'<th>Avg error, points</th></tr></thead><tbody>{scores}</tbody></table></div></div></details>')


def details_card(idx):
    return (f'{chart_card(idx, idx["days"][-30:], 1510)}<div class="card">{_three(idx)}{_why_missed(idx)}'
            f'<p class="plain">{idx["direction"]} Live days scored so far: {idx["live_days"]} of the {idx["days_needed"]} '
            f'needed before the method counts as proven.</p>{_days_table(idx)}'
            f'{_methods(idx, "next session")}{_methods(idx, "in 3 sessions")}</div>')


def _words(data):
    w = data["words"]
    return ('<div class="card"><div class="h first">The words, in numbers</div><dl class="words">'
            f'<dt>most likely</dt><dd>the 50% range: {w["most likely"]}.</dd>'
            f'<dt>almost certainly</dt><dd>the 90% range: {w["almost certainly"]}.</dd>'
            f'<dt>the light</dt><dd>counts days the close stayed inside “almost certainly”: {data["light_rule"]}.</dd></dl>'
            f'<p class="plain">Reasons not checked yet for a miss: {data["not_checked"]}.</p></div>')


def _system(data):
    lines = "".join(f"<li>{s}</li>" for s in data["stricter"])
    checks = "<br>".join(data["checks"]) or "none"
    alerts = "<br>".join(data["alerts"]) or "none today"
    return ('<div class="card"><div class="h first">System</div>'
            f'<p class="plain">Seal checks: {checks}<br>Alerts: {alerts}</p>'
            f'<details class="more"><summary>Stricter checks, last 20 sessions</summary><div class="inner">'
            f'<ul class="lines">{lines}</ul></div></details></div>')


def details(data):
    zoom = (HERE / "zoom.js").read_text()
    cards = "".join(details_card(idx) for idx in data["indices"])
    return (_head(f'Forecast details, {data["report_day"]}', "details") + _header(data) + _overview(data) + cards
            + _words(data) + _system(data) + _foot(data) + f"</div><script>{zoom}</script></body></html>")


def main():
    from pageview import adapt
    page_view = json.loads(next(HERE.glob("pageview-*.json")).read_text())
    data = adapt(page_view)
    (HERE / "fl1-report-picture.html").write_text(picture(data))
    (HERE / "fl1-report-details.html").write_text(details(data))


if __name__ == "__main__":
    main()
