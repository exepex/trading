"""The details page (story FL1-1c v4): the file attached to the message, for whoever wants the numbers behind the
picture. One self-contained file (inline CSS, SVG and a small zoom script, no request), readable from 390 px to
1280 px. It draws a `PageView` and computes nothing; every colour has its glyph or word. The only signal is the
owner's 30-day light (on the picture); the stricter 20-session checks are plain facts here, with no colour."""

from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path

from .grid import hit_grid, score_strip
from .model import Horizon, IndexView, PageView, RangeView
from .simple import chart_block, days_block, misses_block
from .svg import range_bar, timeline_chart
from .zoom import ZOOM_HINT, ZOOM_SCRIPT

STYLES = (Path(__file__).with_name("simple.css"), Path(__file__).with_name("page.css"))
TITLE = "Forecast lab: details"
PAPER = "Paper research only, never an order"
DETAIL_CHART = 1000
WORDS = {"N1": "Next session", "N3": "In 3 sessions"}
LEGEND = (
    '<span class="sw b90"></span>90% range <span class="sw b50"></span>50% range <span class="dot hist"></span>close '
    '<span class="x">&#10007;</span>outside the 90% range'
)
GLOSSARY = (
    '<div class="card"><div class="k">The message&rsquo;s words, in numbers</div><ul class="lines">'
    "<li><b>most likely</b> = the 50% range: a sound method&rsquo;s close lands inside it about 1 day in 2.</li>"
    "<li><b>almost certainly</b> = the 90% range: about 9 days in 10.</li><li><b>right</b> = the next-session close "
    "stayed inside &ldquo;almost certainly&rdquo;. Light: green at 25 or more of the last 30 days, amber at 24, red "
    "at 23 or fewer.</li></ul></div>"
)
NOT_USED = (
    "Reasons not checked yet: overnight US moves (the US closes stay private until the owner approves a display), "
    "FII/DII flows (archived, not yet read here) and the opening gap (no index open price is held)."
)


def day_words(day: date) -> str:
    return f"{day:%a} {day.day} {day:%b}"


def _system(view: PageView) -> str:
    if not view.system:
        return '<div class="banner ok">&#10003; All systems normal.</div>'
    return f'<div class="banner bad">{"".join(f"<div>&#9888; {escape(p)}.</div>" for p in view.system)}</div>'


def _checks(view: PageView) -> str:
    """The stricter 20-session checks as facts, with no colour: the light on the picture is the one signal."""
    facts = "".join(f"<li>{escape(p.group)}, {escape(p.method)}: {escape(p.text)}</li>" for p in view.drift)
    body = facts or "<li>Every method held its ranges within the normal limits over the last 20 sessions.</li>"
    head = '<div class="card"><div class="k">Stricter checks, last 20 sessions</div>'
    return f'{head}<ul class="lines">{body}</ul></div>'


def _today_row(view: RangeView, price: float, low: float, high: float) -> str:
    b = view.band
    return (f'<div class="trow"><div class="tl"><b>{WORDS.get(view.horizon, view.horizon)}</b>'
            f"<span>{day_words(view.target_day)}</span></div>{range_bar(b, price, low, high)}"
            f'<div class="tn"><span>50%</span> <b>{b.q25:,.2f}&ndash;{b.q75:,.2f}</b> &middot; <span>middle</span> '
            f"{b.q50:,.2f} &middot; <span>90%</span> {b.q05:,.2f}&ndash;{b.q95:,.2f}</div></div>")  # fmt: skip


def _exact(index: IndexView) -> str:
    low = min([index.price, *(r.band.q05 for r in index.today)])
    high = max([index.price, *(r.band.q95 for r in index.today)])
    rows = "".join(_today_row(r, index.price, low, high) for r in index.today)
    return (
        f'<div class="card"><div class="k">Exact numbers ({escape(index.method)}, lowest error on its own history, '
        f"the same days it is scored on; "
        f"{index.live_days} of about {index.days_needed} live days scored)</div>"
        f'<div class="price"><b>{index.price:,.2f}</b><span>{escape(index.price_at)}</span></div>{rows}</div>'
    )


def _horizon(horizon: Horizon, underlying: str) -> str:
    t, words = horizon.timeline, WORDS.get(horizon.timeline.horizon, horizon.timeline.horizon).lower()
    chart = ""
    if t.horizon != "N1":
        name = escape(f"{underlying} {words}: closes against the ranges forecast for them")
        chart = (
            f'<div class="wide">{timeline_chart(t, 720, 200, 30, name)}</div>'
            f'<div class="narrow">{timeline_chart(t, 360, 220, 15, name)}</div><p class="legend">{LEGEND}</p>'
        )
    return (f'<div class="card"><div class="k">{escape(underlying)}, {words}: every method by session</div>{chart}'
            f"{hit_grid(horizon.methods)}</div>"
            f'<div class="card"><div class="k">Scores, {words}</div>{score_strip(horizon.methods)}</div>')  # fmt: skip


def _index(index: IndexView) -> str:
    chart = chart_block(index, DETAIL_CHART, f"chart-{index.underlying.lower()}")
    return (f'<section class="index"><h2>{escape(index.underlying)}</h2><div class="card">{chart}'
            f'<p class="explain">{ZOOM_HINT}</p>{days_block(index)}{misses_block(index)}'
            f'<p class="explain">{NOT_USED}</p></div>{_exact(index)}'
            f'{"".join(_horizon(h, index.underlying) for h in index.horizons)}</section>')  # fmt: skip


def _lines(title: str, lines: tuple[str, ...], empty: str) -> str:
    items = "".join(f"<li>{escape(line)}</li>" for line in lines) or f"<li>{empty}</li>"
    return f'<div class="card"><div class="k">{title}</div><ul class="lines">{items}</ul></div>'


def render_page(view: PageView) -> str:
    provenance = "live" if view.provenance.lower().startswith("live") else "preview"
    css = "".join(style.read_text(encoding="utf-8") for style in STYLES)
    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{TITLE}, {day_words(view.day)}</title><style>{css}</style></head>"
        f'<body><div class="wrap"><header class="top"><h1>{TITLE} <span>15:45 &middot; {day_words(view.day)} '
        f'{view.day.year}</span></h1><span class="label paper">{PAPER}</span>'
        f'<span class="label {provenance}">{escape(view.provenance)}</span></header>{_system(view)}{GLOSSARY}'
        f"{''.join(_index(i) for i in view.indices)}{_checks(view)}"
        f"{_lines('Seal checks', view.checks, 'Every forecast sealed in time.')}"
        f"{_lines('Alerts', view.alerts, 'None today.')}"
        f"<footer>{PAPER}.</footer></div><script>{ZOOM_SCRIPT}</script></body></html>\n"
    )
