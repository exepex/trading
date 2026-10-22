"""The picture page (story FL1-1c v3): what a beginner reads on a phone in 30 seconds. Per index, tomorrow's and the
3-day ranges in words and one bar, whether it has been right lately (a light with its words and the last 30 days as
ticks and crosses), and one line on direction; then the system line and "Research only. Not a trade tip." Drawn
560 px wide so the picture stays readable when a phone shrinks it."""

from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path

from .bigchart import big_chart
from .model import IndexView, PageView, RangeView
from .plain import (
    EDITIONS,
    LIGHT_WORDS,
    NORMAL,
    RESEARCH,
    certain,
    day_short,
    light,
    likely,
    record_words,
    result_words,
)

CSS = Path(__file__).with_name("simple.css")
NO_DIRECTION = "It cannot tell up from down yet."
DAYS_NOTE = "&#10003; the close stayed inside &ldquo;almost certainly&rdquo;; &#10007; it did not."
CHART_HEIGHT, PICTURE_CHART = 380, 600
LEGEND = (
    '<span class="sw r50"></span>most likely <span class="sw r90"></span>almost certainly <span class="ln mid"></span>'
    'middle guess <span class="ln close"></span>actual close <span class="hit">&#10003;</span>inside '
    '<span class="miss">&#10007;</span>outside &ldquo;almost certainly&rdquo;'
)
EXPLAIN = (
    "Most likely = a normal day&rsquo;s move (1 day in 2). Almost certainly = covers even a jumpy day (9 days in 10)."
)
MISSES_TITLE = "Last 30 trading days: why it missed"
NO_MISSES = "No misses in the last 30 trading days."


def _when(view: RangeView) -> str:
    return (f'<div class="when"><div class="h">{escape(view.when)}</div>'
            f'<div class="big"><span>most likely</span> {likely(view.band)}</div>'
            f'<div class="sure"><span>almost certainly</span> {certain(view.band)}</div></div>')  # fmt: skip


def chart_block(index: IndexView, width: int, chart_id: str = "") -> str:
    points = index.horizons[0].timeline.points[-30:] if index.horizons else ()
    if not points:
        return ""
    label = escape(f"{index.underlying}: the last {len(points)} closes against the forecast ranges, and the forecasts")
    return (f'<div class="chart">{big_chart(points, index.today, width, CHART_HEIGHT, label, chart_id)}</div>'
            f'<p class="legend">{LEGEND}</p><p class="explain">{EXPLAIN}</p>')  # fmt: skip


def days_block(index: IndexView) -> str:
    points = index.horizons[0].timeline.points[-30:] if index.horizons else ()
    boxes = "".join(f'<div class="d {"ok" if p.inside_90 else "no"}"><b>{"&#10003;" if p.inside_90 else "&#10007;"}'
                    f"</b><span>{p.day.day}<br>{p.day:%b}</span></div>" for p in points)  # fmt: skip
    return f'<div class="days">{boxes}</div><div class="note">{DAYS_NOTE}</div>' if points else ""


def misses_block(index: IndexView) -> str:
    if not index.misses:
        return f'<div class="misses"><div class="h">{MISSES_TITLE}</div><div class="note">{NO_MISSES}</div></div>'
    lines = "".join(f"<li><b>{day_short(m.day)}</b>: closed {m.points:,.0f} points {m.side} &ldquo;almost "
                    f"certainly&rdquo;. <span>Likely reason (after the fact): {escape('; '.join(m.reasons))}.</span>"
                    f"</li>" for m in index.misses)  # fmt: skip
    return f'<div class="misses"><div class="h">{MISSES_TITLE}</div><ul>{lines}</ul></div>'


def _card(index: IndexView, today: date) -> str:
    state = light(index)
    pill = f'<span class="light {state}"><i></i>{LIGHT_WORDS[state]}: {escape(record_words(index))}</span>'
    whens = "".join(_when(r) for r in index.today)
    result = result_words(index, today)
    verdict = f'<div class="note">{escape(result)}</div>' if result else ""
    return (f'<div class="card"><div class="top"><h2>{escape(index.underlying)}<small>{escape(index.price_at)} '
            f'{index.price:,.0f}</small></h2>{pill}</div>{verdict}<div class="whens">{whens}</div>'
            f"{chart_block(index, PICTURE_CHART)}{days_block(index)}{misses_block(index)}"
            f'<div class="note">{NO_DIRECTION}</div></div>')  # fmt: skip


def _status(view: PageView) -> str:
    confirmed = "".join(f'<div class="note">{escape(line)}</div>' for line in view.confirmation)
    if not view.system:
        return f'{confirmed}<div class="status good">{escape(NORMAL)}</div>'
    problems = " ".join(f"&#9888; {escape(problem.rstrip('.'))}." for problem in view.system)
    return f'{confirmed}<div class="status bad">{problems}</div>'


def render_simple(view: PageView) -> str:
    status, (title, at) = _status(view), EDITIONS[view.edition]
    preview = (
        ""
        if view.provenance.lower().startswith("live")
        else f'<span class="tag preview">{escape(view.provenance)}</span>'
    )
    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>Forecast, {day_short(view.day)}'
        f'</title><style>{CSS.read_text(encoding="utf-8")}</style></head><body><div class="wrap">'
        f"<header><h1>{escape(title)} <span>{day_short(view.day)}, {at}</span></h1>{preview}</header>"
        f'{"".join(_card(i, view.day) for i in view.indices)}<div class="card">{status}'
        f'<div class="note">{escape(RESEARCH)}</div></div></div></body></html>\n'
    )
