"""v7: two short editions drawn from the builder's PageView. MORNING, before 09:15: today's forecast for the close
(graph 1). EVENING, after the official close: was the forecast right (graph 2), and the last 10 sessions (graph 3).
`python editions.py` writes fl1-morning.html and fl1-evening.html from the PageView dump next to it."""

import json
from pathlib import Path

from dotchart import DotLayout, DotRangeChart
from linechart import fmt, fmt_high, fmt_low, status
from pageview import adapt
from rangechart import HorizontalRangeChart, RangeLayout, RangeRow

HERE = Path(__file__).parent
WIDTH = 490  # one chart column of the two-column page (1100 px wide; stacked on a phone)
GRID = {"NIFTY": (50, 100), "BANKNIFTY": (100, 200)}  # (hairline every, number every)
DOT_GRID = {"NIFTY": (100, 200), "BANKNIFTY": (250, 500)}
WORD = {"green": "Correct", "amber": "Close call", "red": "Missed"}
GLYPH = {"green": "✓", "amber": "⚠", "red": "✗"}
MEANS = {"green": "closed inside “most likely”", "amber": "closed inside “almost certainly” only",
         "red": "closed outside both ranges"}
RESEARCH = "Research only. Not a trade tip."
# Example values, labelled as such on the page, until the builder wires A17 (cues) and the chain and flow read
# models (levels and flows) into the PageView. Never real numbers posing as today's.
CUES_EXAMPLE = [("S&P 500", "6,412", "−0.6%"), ("Nasdaq 100", "22,180", "−0.9%"), ("US 10-year", "4.21%", "−3 bp"),
                ("USD/INR", "84.62", "+0.1%"), ("Brent (last print)", "$109.8", "+1.2%"),
                ("GIFT Nifty · Asia · Europe", "coming (A17e, A22)", "")]
WHY_MORNING_EXAMPLE = [
    "Option prices imply a normal-sized day: India VIX 13.9, unchanged (example until wired)",
    "Overnight, context only: US −0.4%, Nikkei +0.6%, Hang Seng −0.2% (example until A17e)",
    "No RBI policy, budget or NIFTY expiry today (calendar)"]
LEVELS_EXAMPLE = {"NIFTY": [("Biggest call OI (resistance)", "23,000"), ("Biggest put OI (support)", "22,500"),
                            ("PCR", "0.93 from 1.21"), ("Max pain", "22,900"), ("FII cash, ₹ crore", "−1,250"),
                            ("DII cash, ₹ crore", "+1,800"), ("FII index futures, net contracts", "−2.80 lakh")],
                  "BANKNIFTY": [("Biggest call OI (resistance)", "56,000"), ("Biggest put OI (support)", "55,000"),
                                ("PCR", "0.88 from 1.02"), ("Max pain", "55,500")]}


def _head(title):
    css = (HERE / "editions.css").read_text()
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>'
            f'<style>{css}</style></head><body><div class="wrap">')


def _header(edition, day, issued, data):
    return (f'<header><div><h1>Omenix F&amp;O · {edition}</h1><div class="sub">{day} · issued {issued} IST · '
            f'paper research</div></div><span class="tag">{data["preview_note"]}</span></header>')


def _range_words(f):
    return (f'most likely <b>{fmt_low(f["lo50"])} – {fmt_high(f["hi50"])}</b> · almost certainly '
            f'{fmt_low(f["lo90"])} – {fmt_high(f["hi90"])}')


def _pill(idx):
    if idx["light"] == "none":
        return f'<span class="pill none"><i></i>{idx["light_word"]}</span>'
    return (f'<span class="pill {idx["light"]}"><i></i>{idx["light_word"]}: inside {idx["right30"]} of '
            f'{idx["scored"]} days</span>')


def _foot(data, extra=""):
    system = (" ".join(f'<b class="bad">⚠ {s}</b>' for s in data["system"]) if data["system"]
              else f'<b>✓ {data["system_line"]}</b>')
    return f'<p class="foot">{system} · {RESEARCH}{extra}</p>'


def _key(dot=False):
    marks = ('<span><i class="dot green"></i>✓ inside most likely</span><span><i class="dot amber"></i>⚠ inside almost '
             'certainly only</span><span><i class="dot red"></i>✗ outside both</span>' if dot
             else '<span><i class="dot"></i>last close</span>')
    return (f'<p class="key"><span><i class="r50"></i>most likely (1 day in 2)</span>'
            f'<span><i class="r90"></i>almost certainly (9 days in 10)</span>{marks}</p>')


def _why(title, lines):
    items = "".join(f"<li>{line}</li>" for line in lines)
    return (f'<div class="lab">{title} <span class="when">context, not cause, until a cue feeds the forecaster</span>'
            f'</div><ul class="why-list">{items}</ul>')


def _why_evening(idx, today, st):
    if st == "red":
        reasons = [m["reason"] for m in idx["misses7"] if m["date"].split(" ", 1)[1] == today["date"]]
        gap = (today["close"] - today["hi90"]) if today["close"] > today["hi90"] else (today["lo90"] - today["close"])
        side = "above" if today["close"] > today["hi90"] else "below"
        return [f'Closed {fmt(gap)} points {side} “almost certainly”: ' + (reasons[0] if reasons else
                "no clear reason in our data")] + ["Overnight context: US −1.8%, VIX +9% (example until wired)"]
    width = today["hi90"] - today["lo90"]
    return [f'A {("normal" if st == "green" else "larger than usual")}-sized day: the close moved '
            f'{fmt(abs(today["close"] - today["mid"]))} points from the middle guess, the range was {fmt(width)} wide',
            "Overnight context: US −0.4%, Nikkei +0.6% (example until A17e)"]


def morning_card(idx):
    name, n1, n3 = idx["name"], idx["next"], idx["three"]
    grid, label = GRID[name]
    rows = [RangeRow(f'Close {n1["date"]}', n1, (idx["today"], "ink", "last close")),
            RangeRow(f'In 3 days · {n3["date"]}', n3, None, small=True)]
    chart = HorizontalRangeChart(rows, RangeLayout(WIDTH, grid, label)).svg(f"{name}: today's forecast range")
    return (f'<div class="card"><h2>{name}<small>last close {fmt(idx["today"])} ({idx["price_at"]})</small></h2>'
            f'<div class="lab first">Today’s close, {n1["date"]} <span class="when">our forecast</span></div>'
            f'<div class="headline">{fmt_low(n1["lo50"])} – {fmt_high(n1["hi50"])}<small>most likely</small></div>'
            f'<div class="line">almost certainly <b>{fmt_low(n1["lo90"])} – {fmt_high(n1["hi90"])}</b> · '
            f'middle {fmt(n1["mid"])}</div>'
            f'<div class="lab">Graph 1 · the range on a scale <span class="when">gridlines every {grid} points</span></div>'
            f'<div class="scroll">{chart}</div>{_key()}'
            f'{_why("Why this forecast", WHY_MORNING_EXAMPLE)}'
            f'<div class="lab">3-day outlook · {n3["date"]}</div><div class="line">{_range_words(n3)}</div>'
            f'<div class="record" style="margin-top:10px">{_pill(idx)}<span>right = inside “almost certainly”</span></div>'
            '</div>')


def _cues():
    cells = "".join(f'<div class="cell"><small>{name}</small><b>{value}</b><span>{change}</span></div>'
                    for name, value, change in CUES_EXAMPLE)
    return (f'<div class="card strip"><div class="lab first">Global cues · overnight <span class="when">example values '
            f'until wired (A17)</span></div><div class="cells">{cells}</div></div>')


def morning(data):
    n1 = data["indices"][0]["next"]
    cards = "".join(morning_card(idx) for idx in data["indices"])
    return (_head(f'Morning forecast, {n1["date"]}') + _header("Today’s forecast", n1["date"], "08:50", data)
            + _cues() + f'<div class="cols">{cards}</div>' + _foot(data) + "</div></body></html>")


def evening_card(idx):
    name, days = idx["name"], idx["days"]
    today = days[-1]
    st = status(today)
    grid, label = GRID[name]
    g2 = HorizontalRangeChart([RangeRow(f'Forecast for {today["date_long"]}', today, (today["close"], st, "closed"))],
                              RangeLayout(WIDTH, grid, label)).svg(f"{name}: the forecast range and the close")
    dgrid, dlabel = DOT_GRID[name]
    g3 = DotRangeChart(days[-10:], DotLayout(WIDTH, dgrid, dlabel)).svg(f"{name}: the last 10 sessions")
    return (f'<div class="card"><h2>{name}<small>{today["date_long"]} · closed {fmt(today["close"])}</small></h2>'
            f'<div class="verdict"><span class="chip {st}">{GLYPH[st]} {WORD[st]}</span><div class="facts">'
            f'forecast <b>{fmt_low(today["lo50"])} – {fmt_high(today["hi50"])}</b> · closed <b>{fmt(today["close"])}</b>'
            f'<br>{MEANS[st]}</div></div>{_why("Why it was " + ("wrong" if st == "red" else "right"), _why_evening(idx, today, st))}'
            f'<div class="lab">Graph 2 · today’s range and where it closed <span class="when">gridlines every {grid}</span></div>'
            f'<div class="scroll">{g2}</div>'
            f'<div class="lab">Graph 3 · last 10 sessions <span class="when">each day’s range and its close · gridlines every {dgrid}</span></div>'
            f'<div class="scroll">{g3}</div>{_key(dot=True)}'
            f'<div class="record" style="margin-top:10px">{_pill(idx)}'
            f'<span>wrong days: {", ".join(idx["wrong_days"]) or "none"}</span></div>{_levels(name)}</div>')


def _levels(name):
    rows = "".join(f"<tr><td>{item}</td><td>{value}</td></tr>" for item, value in LEVELS_EXAMPLE[name])
    return (f'<div class="lab">Levels and flows · today’s chain and NSE flows <span class="when">example values until '
            f'wired</span></div><table class="levels"><tbody>{rows}</tbody></table>')


def evening(data):
    today = data["indices"][0]["days"][-1]
    cards = "".join(evening_card(idx) for idx in data["indices"])
    return (_head(f'Evening check, {today["date_long"]}')
            + _header("Was today’s forecast right?", today["date_long"], "20:05", data)
            + f'<div class="cols">{cards}</div>' + _foot(data) + "</div></body></html>")


def main():
    data = adapt(json.loads(next(HERE.glob("pageview-*.json")).read_text()))
    (HERE / "fl1-morning.html").write_text(morning(data))
    (HERE / "fl1-evening.html").write_text(evening(data))


if __name__ == "__main__":
    main()
