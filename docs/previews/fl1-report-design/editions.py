"""v7: two editions, one page each with both indices, drawn from the builder's PageView with ONE chart language
(owner, 21 Oct): the fan chart (corridors and the close line), the reliability trend line and the month calendar.
`python editions.py` writes fl1-morning.html and fl1-evening.html from the PageView dump next to it."""

import json
from pathlib import Path

from calendar_grid import month_grid
from fanchart import FanChart, FanLayout
from linechart import fmt, fmt_high, fmt_low, fmt_mid, status
from pageview import adapt
from trendchart import TrendChart, TrendLayout

HERE = Path(__file__).parent
WIDTH = 490  # one chart column of the two-column page (1100 px wide)
PHONE = 322  # the card's inner width on a 390 px phone: every chart is drawn again at this width, fewer numbers
GRID = {"NIFTY": 100, "BANKNIFTY": 250}
WORD = {"green": "Correct", "amber": "Close call", "red": "Missed"}
GLYPH = {"green": "✓", "amber": "⚠", "red": "✗"}
MEANS = {"green": "closed inside “most likely”", "amber": "closed inside “almost certainly” only",
         "red": "closed outside both ranges"}
WHY_TITLE = {"green": "Why it was correct", "amber": "Why a close call", "red": "Why it missed"}
RESEARCH = "Research only. Not a trade tip."
# Example values, labelled as such on the page, until the builder wires A17 (cues), VIX and the chain and flow read
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


def _foot(data):
    system = (" ".join(f'<b class="bad">⚠ {s}</b>' for s in data["system"]) if data["system"]
              else f'<b>✓ {data["system_line"]}</b>')
    return f'<p class="foot">{system} · {RESEARCH}</p>'


def _key():
    return ('<p class="key"><span><i class="r50"></i>most likely (1 day in 2)</span>'
            '<span><i class="r90"></i>almost certainly (9 days in 10)</span><span><i class="ln"></i>actual close</span>'
            '<span class="nowrap"><i class="dot green"></i>✓ correct · <i class="dot amber"></i>⚠ close call · '
            '<i class="dot red"></i>✗ missed</span></p>')


def _why(title, lines):
    items = "".join(f"<li>{line}</li>" for line in lines)
    return (f'<div class="lab">{title} <span class="when">context, not cause, until a cue feeds the forecaster</span>'
            f'</div><ul class="why-list">{items}</ul>')


def _trend(idx, width=WIDTH):
    days = idx["days"][-len(idx["rolling_90"]):] if idx["rolling_90"] else idx["days"][-30:]
    return TrendChart([d["date"] for d in days], idx["rolling_90"], TrendLayout(width))


def _both(desk, phone):
    """The desktop drawing and the phone drawing of one chart; CSS shows one of them."""
    return f'<div class="desk">{desk}</div><div class="phone">{phone}</div>'


def _reliability_chip(idx):
    """One definition of right everywhere: inside "almost certainly"; the colour follows the trend's state."""
    state = _trend(idx).state()
    if idx["light"] == "none":
        return f'<span class="pill none"><i></i>{idx["light_word"]}</span>'
    days = idx["days"][-idx["scored"]:]
    correct = sum(status(d) == "green" for d in days)
    close = sum(status(d) == "amber" for d in days)
    colour = {"steady": "green", "watch": "amber"}.get(state, "none")
    return (f'<span class="pill {colour}"><i></i>Inside “almost certainly” {idx["right30"]} of {idx["scored"]} '
            f'(✓ correct {correct} · ⚠ close call {close}) · {state}</span>')


# ---- morning ---------------------------------------------------------------------------------------------------

def _cues():
    cells = "".join(f'<div class="cell"><small>{name}</small><b>{value}</b><span>{change}</span></div>'
                    for name, value, change in CUES_EXAMPLE)
    return (f'<div class="card strip"><div class="lab first">Global cues · overnight <span class="when">example values '
            f'until wired (A17)</span></div><div class="cells">{cells}</div></div>')


def morning_card(idx):
    name, n1, n3 = idx["name"], idx["next"], idx["three"]
    aria = f"{name}: last 10 days and today’s forecast corridor"
    fan = FanChart(idx["days"][-10:], FanLayout(WIDTH, GRID[name], forecast_width=96), forecast=n1, date_every=2)
    small = FanChart(idx["days"][-10:], FanLayout(PHONE, GRID[name], plot_height=190, axis_width=44, forecast_width=78),
                     forecast=n1, date_every=3)
    return (f'<div class="card"><h2>{name}<small>last close {fmt(idx["today"])} ({idx["price_at"]})</small></h2>'
            f'<div class="lab first">Today’s forecast · close {n1["date"]}</div>'
            f'<div class="headline">{fmt_low(n1["lo50"])} – {fmt_high(n1["hi50"])}<small>most likely</small></div>'
            f'<div class="line">almost certainly <b>{fmt_low(n1["lo90"])} – {fmt_high(n1["hi90"])}</b> · '
            f'middle {fmt_mid(n1["mid"])} · in 3 days most likely {fmt_low(n3["lo50"])} – {fmt_high(n3["hi50"])}</div>'
            f'<div class="lab">Last 10 days and today’s corridor <span class="when">gridlines every {GRID[name]}</span></div>'
            f'{_both(fan.svg(aria), small.svg(aria))}{_key()}'
            f'{_why("Why this forecast", WHY_MORNING_EXAMPLE)}'
            f'<div class="record">{_reliability_chip(idx)}<span>steady = the 20-day share inside “almost certainly” '
            f'holds 80% or more; watch = it does not</span></div></div>')


def morning(data):
    n1 = data["indices"][0]["next"]
    cards = "".join(morning_card(idx) for idx in data["indices"])
    return (_head(f'Morning forecast, {n1["date"]}') + _header("Today’s forecast", n1["date"], "08:50", data)
            + _cues() + f'<div class="cols">{cards}</div>' + _foot(data) + "</div></body></html>")


# ---- evening ---------------------------------------------------------------------------------------------------

def _why_evening(idx, today, st):
    if st == "red":
        reasons = [m["reason"] for m in idx["misses7"] if m["date"].split(" ", 1)[1] == today["date"]]
        gap = (today["close"] - today["hi90"]) if today["close"] > today["hi90"] else (today["lo90"] - today["close"])
        side = "above" if today["close"] > today["hi90"] else "below"
        return [f'Closed {fmt(gap)} points {side} “almost certainly”: ' + (reasons[0] if reasons else
                "no clear reason in our data"), "Overnight context: US −1.8%, VIX +9% (example until wired)"]
    size = "normal" if st == "green" else "larger than usual"
    return [f'A {size}-sized day: the close moved {fmt(abs(today["close"] - today["mid"]))} points from the middle '
            f'guess; the “almost certainly” range was {fmt(today["hi90"] - today["lo90"])} wide',
            "Overnight context: US −0.4%, Nikkei +0.6% (example until A17e)"]


def _misses_table(idx):
    rows = []
    for d in reversed(idx["days"][-30:]):
        if status(d) != "red":
            continue
        gap = d["close"] - d["hi90"] if d["close"] > d["hi90"] else d["lo90"] - d["close"]
        side = "above" if d["close"] > d["hi90"] else "below"
        reason = next((m["reason"] for m in idx["misses7"] if m["date"].split(" ", 1)[1] == d["date"]), None)
        rows.append(f'<tr><td>{d["date"]}</td><td>{fmt(gap)} {side}</td>'
                    f'<td>{reason or "<i>reason kept for the last 7 days only (builder to extend)</i>"}</td></tr>')
    body = "".join(rows) or '<tr><td colspan="3">No miss in the last 30 days.</td></tr>'
    return ('<table class="misses"><thead><tr><th>Date</th><th>Outside by</th><th>Reason</th></tr></thead>'
            f'<tbody>{body}</tbody></table>')


def _levels(name):
    rows = "".join(f"<tr><td>{item}</td><td>{value}</td></tr>" for item, value in LEVELS_EXAMPLE[name])
    return f'<table class="levels"><tbody>{rows}</tbody></table>'


def evening_card(idx, issue_day):
    name, days = idx["name"], idx["days"]
    today = days[-1]
    st = status(today)
    aria = f"{name}: the last 30 days, forecast corridors and the close"
    fan = FanChart(days[-30:], FanLayout(WIDTH, GRID[name], plot_height=260), date_every=5)
    small = FanChart(days[-30:], FanLayout(PHONE, GRID[name], plot_height=220, axis_width=44), date_every=7)
    trend, trend_small = _trend(idx), _trend(idx, PHONE)
    return (f'<div class="card"><h2>{name}<small>{today["date_long"]} · closed {fmt(today["close"])}</small></h2>'
            f'<div class="verdict"><span class="chip {st}">{GLYPH[st]} {WORD[st]}</span><div class="facts">'
            f'forecast <b>{fmt_low(today["lo50"])} – {fmt_high(today["hi50"])}</b> · closed <b>{fmt(today["close"])}</b>'
            f'<br>{MEANS[st]}</div></div>'
            f'{_why(WHY_TITLE[st], _why_evening(idx, today, st))}'
            f'<div class="lab">Last 30 days · forecast vs actual <span class="when">gridlines every {GRID[name]}, '
            f'a number every {GRID[name] * fan.label_every}</span></div>'
            f'{_both(fan.svg(aria), small.svg(aria))}{_key()}'
            f'<div class="lab">This month · right vs wrong</div>{month_grid(days, issue_day)}'
            f'<div class="lab">Reliability trend <span class="when">20-day share inside “almost certainly” · '
            f'{trend.state()}</span></div>'
            f'{_both(trend.svg(f"{name}: reliability trend"), trend_small.svg(f"{name}: reliability trend"))}'
            f'<div class="lab">When it was wrong · last 30 days</div>{_misses_table(idx)}'
            f'<div class="lab">Levels and flows · today’s chain and NSE flows <span class="when">example values until '
            f'wired</span></div>{_levels(name)}</div>')


def evening(data):
    today = data["indices"][0]["days"][-1]
    issue_day = max(d["iso"] for d in data["indices"][0]["days"])
    from datetime import date
    cards = "".join(evening_card(idx, date.fromisoformat(issue_day)) for idx in data["indices"])
    return (_head(f'Evening check, {today["date_long"]}')
            + _header("Was today’s forecast right?", today["date_long"], "20:05", data)
            + f'<div class="cols">{cards}</div>' + _foot(data) + "</div></body></html>")


def main():
    data = adapt(json.loads(next(HERE.glob("pageview-*.json")).read_text()))
    (HERE / "fl1-morning.html").write_text(morning(data))
    (HERE / "fl1-evening.html").write_text(evening(data))


if __name__ == "__main__":
    main()
