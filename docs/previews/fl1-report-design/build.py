"""Builds the two preview pages (the picture and the details) from data_v4.json. Standard library only:
`python build.py` writes fl1-report-picture.html and fl1-report-details.html next to it."""

import json
from pathlib import Path

from chart import Layout, RangeColumnChart, fmt, fmt_high, fmt_low

HERE = Path(__file__).parent
PICTURE_DAYS = 10
ZOOM_SCRIPT = (HERE / "zoom.js").read_text()


def _head(title, body_class=""):
    css = (HERE / "report.css").read_text()
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>'
            f'<style>{css}</style></head><body class="{body_class}"><div class="wrap">')


def _header(data):
    return (f'<header><h1>Forecast <span>{data["report_day"]}, {data["report_time"]}</span></h1>'
            f'<span class="tag">{data["preview_note"]}</span></header>')


def _range(f):
    return f'{fmt_low(f["lo50"])} – {fmt_high(f["hi50"])}', f'{fmt_low(f["lo90"])} – {fmt_high(f["hi90"])}'


def _forecast_block(idx):
    likely, sure = _range(idx["next"])
    likely3, sure3 = _range(idx["three"])
    return (f'<div class="fc"><div class="next"><div class="h">Next trading day · {idx["next"]["date"]}</div>'
            f'<div class="big"><span>most likely</span>{likely}</div>'
            f'<div class="sure"><span>almost certainly</span>{sure}</div></div>'
            f'<div class="three"><div class="h">In 3 trading days · {idx["three"]["date"]}</div>'
            f'<div class="big"><span>most likely</span>{likely3}</div>'
            f'<div class="sure"><span>almost certainly</span>{sure3}</div></div></div>')


def _light(idx):
    word = {"green": "Good", "amber": "Watch", "red": "Poor"}[idx["light"]]
    return f'<span class="light {idx["light"]}"><i></i>{word}: right {idx["right30"]} of the last 30 days</span>'


def _key():
    return ('<p class="key"><span><i class="r50"></i>most likely</span><span><i class="r90"></i>almost certainly</span>'
            '<span><i class="dot"></i>where it closed</span>'
            '<span><b class="ok">✓</b> inside · <b class="miss">✗</b> outside “almost certainly”</span></p>'
            '<p class="plain">Most likely = a normal day’s move (1 day in 2). '
            'Almost certainly = covers even a jumpy day (9 days in 10).</p>')


def _wrong_line(idx, days):
    misses = [d["date"] for d in reversed(days) if not d["right"]]
    if not misses:
        return f'<p class="wrong"><b class="ok">Right on all of the last {len(days)} trading days.</b></p>'
    return (f'<p class="wrong">Wrong on <b class="miss">{len(misses)} of the last {len(days)} trading days</b>: '
            f'{", ".join(misses)}. Right on every other day.</p>')


def _why_missed(idx):
    items = idx["misses7"]
    if not items:
        body = '<ul class="why"><li>No misses in the last 7 trading days.</li></ul>'
    else:
        body = '<ul class="why">' + "".join(
            f'<li><b>{m["date"]}</b>: closed {m["points"]} points {m["side"]} “almost certainly”. '
            f'<span>Likely reason, after the fact: {m["reason"]}.</span></li>' for m in items) + "</ul>"
    return '<div class="h">Why it missed · last 7 trading days</div>' + body


def _chart(idx, days, width, label_every):
    forecasts = [("next day", idx["next"]), ("in 3 days", idx["three"])]
    chart = RangeColumnChart(days, forecasts, Layout(width=width), label_every=label_every)
    aria = f'{idx["name"]}: each day’s forecast range and where it closed, then the forecasts'
    return chart.svg(aria)


def _card_top(idx):
    return (f'<div class="top"><h2>{idx["name"]}<small>closed today at {fmt(idx["today"])}</small></h2>'
            f'{_light(idx)}</div>')


def picture_card(idx):
    days = idx["days"][-PICTURE_DAYS:]
    return (f'<div class="card">{_card_top(idx)}{_forecast_block(idx)}'
            f'<div class="h">Last {PICTURE_DAYS} trading days · forecast range and where it closed</div>'
            f'{_chart(idx, days, 568, 1)}{_key()}{_wrong_line(idx, idx["days"])}{_why_missed(idx)}</div>')


def _foot(data):
    return (f'<div class="foot"><span class="ok">✓ {data["system_line"]}</span>'
            f'<span class="research">{data["research_line"]}</span></div>')


def picture(data, only=None):
    """The whole picture, or one index's picture when `only` names it (one image per index previews better in Slack)."""
    cards = "".join(picture_card(idx) for idx in data["indices"] if only in (None, idx["name"]))
    return _head(f'Forecast, {data["report_day"]}') + _header(data) + cards + _foot(data) + "</div></body></html>"


def _days_table(idx):
    rows = []
    for d in reversed(idx["days"]):
        cls = "ok" if d["right"] else "miss"
        mark = "✓ inside" if d["right"] else "✗ outside"
        rows.append(f'<tr class="{cls}"><td>{d["date"]}</td><td>{fmt(d["lo90"])} – {fmt(d["hi90"])}</td>'
                    f'<td>{fmt(d["lo50"])} – {fmt(d["hi50"])}</td><td>{fmt(d["mid"])}</td>'
                    f'<td>{fmt(d["close"])}</td><td class="{cls}">{mark}</td></tr>')
    return ('<div class="h">Every day in numbers · forecast made the session before</div><div class="scroll">'
            '<table class="days"><thead><tr><th>Day</th><th>Almost certainly</th><th>Most likely</th>'
            '<th>Middle</th><th>Closed</th><th>Right?</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>")


def _methods(idx, horizon):
    block = idx["methods"][horizon]
    dates = [d["date"] for d in idx["days"]]
    head = "".join(f"<th>{d.split()[0]}</th>" for d in dates)
    glyph = {"in50": "✓", "in90": "✓", "miss": "✗", "none": "·"}
    grid = "".join(
        f'<tr><th class="m">{m}{" ★" if m == "implied" else ""}</th>'
        + "".join(f'<td class="{c}">{glyph[c]}</td>' for c in cells) + "</tr>"
        for m, cells in block["grid"].items())
    scores = "".join(
        f'<tr><td>{s["method"]}{" ★" if s["method"] == "implied" else ""}</td><td>{s["in50"]}</td>'
        f'<td>{s["in90"]}</td><td>{s["err"]}</td></tr>' for s in block["scores"])
    months = f'{dates[0].split()[1]} → {dates[-1].split()[1]}'
    return (f'<details class="more"><summary>Every method, {horizon} (for the curious)</summary><div class="inner">'
            f'<div class="scroll"><table class="hits"><thead><tr><th class="m">{months}</th>{head}</tr></thead>'
            f'<tbody>{grid}</tbody></table></div>'
            '<p class="plain">Bright ✓ inside the 50% range, pale ✓ inside the 90% range only, ✗ outside both. '
            '★ = the method shown in the report: best on history, not yet proven live.</p>'
            '<div class="scroll"><table class="scores"><thead><tr><th>Method</th>'
            '<th>In 50% range<br>7 · 14 · 30 days</th><th>In 90% range<br>7 · 14 · 30 days</th>'
            f'<th>Avg error, points</th></tr></thead><tbody>{scores}</tbody>'
            '</table></div></div></details>')


def _exact(idx):
    n, t = idx["next"], idx["three"]
    def line(f):
        return (f'50% {f["lo50"]:,.2f}–{f["hi50"]:,.2f} · middle {f["mid"]:,.2f} · '
                f'90% {f["lo90"]:,.2f}–{f["hi90"]:,.2f}')
    return (f'<details class="more"><summary>Exact forecast numbers</summary><div class="inner"><dl class="words">'
            f'<dt>Next session, {n["date"]}</dt><dd>{line(n)}</dd><dt>In 3 sessions, {t["date"]}</dt><dd>{line(t)}</dd>'
            f'<dt>Today, 3 pm</dt><dd>{idx["today"]:,}</dd></dl></div></details>')


def details_card(idx):
    return (f'<div class="card">{_card_top(idx)}{_forecast_block(idx)}'
            f'<div class="h">Last 30 trading days · forecast range and where it closed</div>'
            f'<div class="scroll">{_chart(idx, idx["days"], 1060, 1)}</div>{_key()}'
            '<p class="zoom">Zoom: scroll or pinch on the chart, drag to move, double-tap to reset. '
            'On a phone the chart also scrolls sideways.</p>'
            f'{_wrong_line(idx, idx["days"])}{_why_missed(idx)}'
            f'<p class="plain">{idx["direction"]}</p>'
            f'{_days_table(idx)}{_exact(idx)}{_methods(idx, "next session")}{_methods(idx, "in 3 sessions")}</div>')


def _words(data):
    w = data["words"]
    return ('<div class="card"><div class="h" style="margin-top:0">The words, in numbers</div><dl class="words">'
            f'<dt>most likely</dt><dd>the 50% range: {w["most likely"]}.</dd>'
            f'<dt>almost certainly</dt><dd>the 90% range: {w["almost certainly"]}.</dd>'
            f'<dt>right</dt><dd>{w["right"]}. The light is {data["light_rule"]}.</dd></dl>'
            f'<p class="plain">Reasons not checked yet for a miss: {data["not_checked"]}.</p></div>')


def _system(data):
    lines = "".join(f"<li>{s}</li>" for s in data["stricter"])
    return ('<div class="card"><div class="h" style="margin-top:0">System</div>'
            f'<p class="plain">Seal checks: {data["seal"]}<br>Alerts: {data["alerts"]}</p>'
            f'<details class="more"><summary>Stricter checks, last 20 sessions</summary><div class="inner">'
            f'<ul class="lines">{lines}</ul></div></details></div>')


def details(data):
    cards = "".join(details_card(idx) for idx in data["indices"])
    return (_head(f'Forecast details, {data["report_day"]}', "details") + _header(data) + _foot(data) + cards
            + _words(data) + _system(data) + _foot(data) + f"</div><script>{ZOOM_SCRIPT}</script></body></html>")


def main():
    data = json.loads((HERE / "data_v4.json").read_text())
    (HERE / "fl1-report-picture.html").write_text(picture(data))
    for idx in data["indices"]:
        (HERE / f"fl1-report-picture-{idx['name'].lower()}.html").write_text(picture(data, only=idx["name"]))
    (HERE / "fl1-report-details.html").write_text(details(data))


if __name__ == "__main__":
    main()
