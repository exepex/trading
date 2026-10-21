"""v8: two editions, one page each with both indices, no shaded bands and no bars (owner, 21 Oct). Evening per
index: the result card (three big numbers), chart 1 (forecast middle vs actual close), chart 2 (how far off),
the day-by-day table, the counts with percentages and the calendar, the reliability trend, the misses, the levels.
Morning per index: the big numbers, chart 1 over 10 days with today's forecast on the right, the reasons, the chip.
`python editions.py` writes fl1-morning.html and fl1-evening.html from the PageView dump next to it."""

import json
from datetime import date
from pathlib import Path

from blocks import WORD, counts_line, day_table, misses_table, month_block, result_card
from gapchart import GapChart, GapLayout
from linechart import fmt, fmt_high, fmt_low, fmt_mid, status
from pageview import adapt
from trendchart import TrendChart, TrendLayout
from twolines import LinesLayout, TwoLinesChart

HERE = Path(__file__).parent
WIDE, PHONE = 1060, 338  # one chart per row: the card's inner width on desktop and on a 390 px phone
GRID = {"NIFTY": 100, "BANKNIFTY": 250}
RESEARCH = "Research only. Not a trade tip."
WHY_TITLE = {"green": "Why it was correct", "amber": "Why a close call", "red": "Why it missed"}
# Example values, labelled as such on the page, until the builder wires A17 (cues), VIX and the chain and flow
# read models (FL1-1d's SectionView and Cue). Never real numbers posing as today's.
CUES_EXAMPLE = [("S&P 500", "6,412", "−0.6%"), ("Nasdaq 100", "22,180", "−0.9%"), ("US 10-year", "4.21%", "−3 bp"),
                ("USD/INR", "84.62", "+0.1%"), ("Brent (last print)", "$109.8", "+1.2%"),
                ("GIFT Nifty · Asia · Europe", "not available", "")]
WHY_MORNING_EXAMPLE = [
    "Option prices imply a normal-sized day: India VIX 13.9, unchanged (context; example until wired)",
    "Overnight, context only: US −0.4%, Nikkei +0.6%, Hang Seng −0.2% (example until A17e)",
    "No RBI policy, budget or NIFTY expiry today (calendar)"]
LEVELS_EXAMPLE = {"NIFTY": [("Biggest call OI (resistance)", "23,000"), ("Biggest put OI (support)", "22,500"),
                            ("PCR", "0.93 from 1.21"), ("Max pain", "22,900"), ("FII cash, ₹ crore", "−1,250"),
                            ("DII cash, ₹ crore", "+1,800"), ("FII index futures, net contracts", "−2.80 lakh")],
                  "BANKNIFTY": [("Biggest call OI (resistance)", "56,000"), ("Biggest put OI (support)", "55,000"),
                                ("PCR", "0.88 from 1.02"), ("Max pain", "55,500")]}
KEY = ('<div class="card howto"><b>How to read the result.</b> ✓ Correct = closed inside “most likely” (1 day in 2). '
       '⚠ Close call = outside “most likely” but inside “almost certainly” (9 days in 10). ✗ Missed = outside '
       '“almost certainly”. The gap says how far and which way: + closed higher than the forecast middle, − lower.</div>')


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


def _both(desk, phone):
    """The desktop drawing and the phone drawing of one chart; CSS shows one of them."""
    return f'<div class="desk">{desk}</div><div class="phone">{phone}</div>'


def _why(title, lines):
    items = "".join(f"<li>{line}</li>" for line in lines)
    return (f'<div class="lab">{title} <span class="when">context, not cause, until a cue feeds the forecaster</span>'
            f'</div><ul class="why-list">{items}</ul>')


def _trend(idx, width):
    days = idx["days"][-len(idx["rolling_90"]):] if idx["rolling_90"] else idx["days"][-30:]
    return TrendChart([d["date"] for d in days], idx["rolling_90"], TrendLayout(width))


def _chip(idx):
    state = _trend(idx, WIDE).state()
    if idx["light"] == "none":
        return f'<span class="pill none"><i></i>{idx["light_word"]}</span>'
    days = idx["days"][-idx["scored"]:]
    correct, close = sum(status(d) == "green" for d in days), sum(status(d) == "amber" for d in days)
    colour = {"steady": "green", "watch": "amber"}.get(state, "none")
    return (f'<span class="pill {colour}"><i></i>Inside “almost certainly” {idx["right30"]} of {idx["scored"]} '
            f'(✓ correct {correct} · ⚠ close call {close}) · {state}</span>')


def _lines_key(morning=False):
    extra = ('<span><i class="ln r50"></i>most likely</span><span><i class="ln r90"></i>almost certainly</span>'
             if morning else "")
    return (f'<p class="key"><span><i class="ln mid"></i>forecast middle</span><span><i class="ln close"></i>actual close</span>'
            f'<span class="nowrap"><i class="dot green"></i>✓ correct · <i class="dot amber"></i>⚠ close call · '
            f'<i class="dot red"></i>✗ missed</span>{extra}</p>')


# ---- morning ---------------------------------------------------------------------------------------------------

def _cues():
    cells = "".join(f'<div class="cell"><small>{name}</small><b>{value}</b><span>{change}</span></div>'
                    for name, value, change in CUES_EXAMPLE)
    return (f'<div class="card strip"><div class="lab first">Global cues · overnight <span class="when">example values '
            f'until wired (A17); “not out yet” and “not available” are written as plain words</span></div>'
            f'<div class="cells">{cells}</div></div>')


def morning_section(idx):
    name, n1, n3 = idx["name"], idx["next"], idx["three"]
    aria = f"{name}: forecast middle and actual close, last 10 days, with today's forecast"
    desk = TwoLinesChart(idx["days"][-10:], LinesLayout(WIDE, GRID[name], forecast_width=150), forecast=n1)
    phone = TwoLinesChart(idx["days"][-10:], LinesLayout(PHONE, GRID[name], plot_height=200, axis_width=46,
                                                         forecast_width=74), forecast=n1, date_every=3)
    return (f'<div class="card"><h2>{name}<small>last close {fmt(idx["today"])} ({idx["price_at"]})</small></h2>'
            f'<div class="lab first">Today’s forecast · close {n1["date"]}</div>'
            f'<div class="three big"><div><small>Most likely</small><b>{fmt_low(n1["lo50"])} – {fmt_high(n1["hi50"])}</b>'
            f'<span>1 day in 2</span></div><div><small>Almost certainly</small><b>{fmt_low(n1["lo90"])} – '
            f'{fmt_high(n1["hi90"])}</b><span>9 days in 10</span></div><div><small>Forecast middle</small>'
            f'<b>{fmt_mid(n1["mid"])}</b><span>in 3 days most likely {fmt_low(n3["lo50"])} – {fmt_high(n3["hi50"])}</span>'
            f'</div></div></div>'
            f'<div class="card"><div class="lab first">{name} · forecast vs actual close, last 10 days, and today’s '
            f'forecast <span class="when">gridlines every {GRID[name]}</span></div>'
            f'{_both(desk.svg(aria), phone.svg(aria))}{_lines_key(morning=True)}</div>'
            f'<div class="card">{_why("Why this forecast", WHY_MORNING_EXAMPLE)}'
            f'<div class="record">{_chip(idx)}<span>steady = the 20-day share inside “almost certainly” holds 80% or '
            f'more; watch = it does not</span></div></div>')


def morning(data):
    n1 = data["indices"][0]["next"]
    body = "".join(morning_section(idx) for idx in data["indices"])
    return (_head(f'Morning forecast, {n1["date"]}') + _header("Today’s forecast", n1["date"], "08:50", data)
            + KEY + _cues() + body + _foot(data) + "</div></body></html>")


# ---- evening ---------------------------------------------------------------------------------------------------

def _why_evening(idx, today, st):
    if st == "red":
        reasons = [m["reason"] for m in idx["misses7"] if m["date"].split(" ", 1)[1] == today["date"]]
        return [reasons[0] if reasons else "No clear reason in our data",
                "Overnight context: US −1.8%, VIX +9% (example until wired)"]
    size = "normal" if st == "green" else "larger than usual"
    return [f'A {size}-sized day: the close moved {fmt(abs(today["close"] - today["mid"]))} points from the forecast '
            f'middle; “almost certainly” was {fmt(today["hi90"] - today["lo90"])} points wide',
            "Overnight context: US −0.4%, Nikkei +0.6% (example until A17e)"]


def _levels(name):
    rows = "".join(f"<tr><td>{item}</td><td>{value}</td></tr>" for item, value in LEVELS_EXAMPLE[name])
    return f'<table class="levels"><tbody>{rows}</tbody></table>'


def evening_section(idx, issue_day):
    name, days = idx["name"], idx["days"][-30:]
    today, grid = days[-1], GRID[name]
    st = status(today)
    a1 = f"{name}: forecast middle and actual close, last 30 days"
    a2 = f"{name}: how far the close was from the forecast middle, last 30 days"
    c1 = _both(TwoLinesChart(days, LinesLayout(WIDE, grid), date_every=3).svg(a1),
               TwoLinesChart(days, LinesLayout(PHONE, grid, plot_height=200, axis_width=46), date_every=7).svg(a1))
    c2 = _both(GapChart(days, GapLayout(WIDE, grid), date_every=3).svg(a2),
               GapChart(days, GapLayout(PHONE, grid, plot_height=200, axis_width=46), date_every=7).svg(a2))
    trend = _both(_trend(idx, WIDE).svg(f"{name}: reliability trend"), _trend(idx, PHONE).svg(f"{name}: reliability trend"))
    return (f'<div class="card"><h2>{name}<small>{today["date_long"]} · closed {fmt(today["close"])}</small></h2>'
            f'{result_card(today)}{_why(WHY_TITLE[st], _why_evening(idx, today, st))}</div>'
            f'<div class="card"><div class="lab first">{name} · chart 1 · forecast vs actual close, last 30 days '
            f'<span class="when">gridlines every {grid}</span></div>{c1}{_lines_key()}</div>'
            f'<div class="card"><div class="lab first">{name} · chart 2 · how far off, last 30 days '
            f'<span class="when">actual close minus the forecast middle, in points · above zero = closed higher than '
            f'forecast · dashed = the range edges</span></div>'
            f'{c2}<p class="key"><span><i class="ln r50"></i>most likely edges</span><span><i class="ln r90"></i>almost '
            f'certainly edges</span><span class="nowrap"><i class="dot green"></i>✓ · <i class="dot amber"></i>⚠ · '
            f'<i class="dot red"></i>✗</span></p></div>'
            f'<div class="card"><div class="lab first">{name} · day by day, last 10 sessions</div>{day_table(idx, days[-10:])}</div>'
            f'<div class="card"><div class="lab first">{name} · right vs wrong</div>'
            f'{counts_line(days, "trading days, the last 30")}{month_block(idx["days"], issue_day)}</div>'
            f'<div class="card"><div class="lab first">{name} · reliability trend <span class="when">20-day share inside '
            f'“almost certainly” · {_trend(idx, WIDE).state()}</span></div>{trend}</div>'
            f'<div class="card"><div class="lab first">{name} · when it was wrong, last 30 days</div>{misses_table(idx, days)}'
            f'<div class="lab">Levels and flows · today’s chain and NSE flows <span class="when">example values until '
            f'wired</span></div>{_levels(name)}</div>')


def evening(data):
    today = data["indices"][0]["days"][-1]
    issue_day = date.fromisoformat(max(d["iso"] for d in data["indices"][0]["days"]))
    body = "".join(evening_section(idx, issue_day) for idx in data["indices"])
    return (_head(f'Evening check, {today["date_long"]}')
            + _header("Was today’s forecast right?", today["date_long"], "20:05", data)
            + KEY + body + _foot(data) + "</div></body></html>")


def main():
    data = adapt(json.loads(next(HERE.glob("pageview-*.json")).read_text()))
    (HERE / "fl1-morning.html").write_text(morning(data))
    (HERE / "fl1-evening.html").write_text(evening(data))


if __name__ == "__main__":
    main()
