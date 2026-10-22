"""Edition A, 08:50 IST, "Today's forecast": the key, the cues strip, then per index the three big numbers, chart 1
over the last 10 sessions with today's forecast on the right, "why this forecast" and the reliability chip."""

from __future__ import annotations

from ..page.model import IndexView, PageView
from .formats import fmt, fmt_mid, fmt_range
from .lines_chart import LinesChart, LinesLayout
from .page import KEY, PHONE, WIDE, both, cues_strip, foot, head, header, method_line, reliability_chip, why_block
from .values import days_of, today_of

TITLE, ISSUED = "Today’s forecast", "08:50"
GRID = {"NIFTY": 100, "BANKNIFTY": 250}
DEFAULT_GRID = 100
SHOWN = 10
NO_FORECAST = "no forecast sealed for today"


def big_numbers(index: IndexView) -> str:
    n1, n3 = today_of(index, "N1"), today_of(index, "N3")
    if n1 is None:
        return f'<div class="lab first">Today’s forecast</div><div class="line">{NO_FORECAST}</div>'
    outlook = f"in 3 days most likely {fmt_range(n3.lo50, n3.hi50)}" if n3 else ""
    return (
        f'<div class="lab first">Today’s forecast · close {n1.date}</div><div class="three big">'
        f"<div><small>Most likely</small><b>{fmt_range(n1.lo50, n1.hi50)}</b><span>1 day in 2</span></div>"
        f"<div><small>Almost certainly</small><b>{fmt_range(n1.lo90, n1.hi90)}</b><span>9 days in 10</span></div>"
        f"<div><small>Forecast middle</small><b>{fmt_mid(n1.mid)}</b><span>{outlook}</span></div></div>"
    )


def chart_card(index: IndexView) -> str:
    name, days, n1 = index.underlying, days_of(index, SHOWN), today_of(index, "N1")
    if not days:
        return ""
    grid = GRID.get(name, DEFAULT_GRID)
    aria = f"{name}: forecast middle and actual close, last {len(days)} days, with today's forecast"
    desk = LinesChart(days, LinesLayout(WIDE, grid, forecast_width=150), forecast=n1)
    phone = LinesChart(days, LinesLayout(PHONE, grid, plot_height=200, axis_width=46, forecast_width=74),
                       forecast=n1, date_every=3)  # fmt: skip
    key = (
        '<p class="key"><span><i class="ln mid"></i>forecast middle</span><span><i class="ln close"></i>actual close'
        '</span><span class="nowrap"><i class="dot green"></i>✓ correct · <i class="dot amber"></i>⚠ close call · '
        '<i class="dot red"></i>✗ missed</span><span><i class="ln r50"></i>most likely</span>'
        '<span><i class="ln r90"></i>almost certainly</span></p>'
    )
    return (
        f'<div class="card"><div class="lab first">{name} · forecast vs actual close, last {len(days)} days, and '
        f'today’s forecast <span class="when">gridlines every {grid}</span></div>'
        f"{both(desk.svg(aria), phone.svg(aria))}{key}</div>"
    )


def section(index: IndexView) -> str:
    name, days = index.underlying, days_of(index, SHOWN)
    return (
        f'<div class="card"><h2>{name}<small>last close {fmt(index.price)} ({index.price_at})</small></h2>'
        f"{big_numbers(index)}</div>{chart_card(index)}"
        f'<div class="card">{why_block("Why this forecast", [], index)}'
        f'<div class="record">{reliability_chip(index, days)}</div>{method_line(index)}</div>'
    )


def render_morning(view: PageView) -> str:
    n1 = next((today_of(i, "N1") for i in view.indices if today_of(i, "N1")), None)
    day = n1.date if n1 else f"{view.day:%a} {view.day.day} {view.day:%b}"
    confirmation = "".join(f'<p class="confirm">{line}</p>' for line in getattr(view, "confirmation", ()))
    body = "".join(section(index) for index in view.indices)
    return (
        head(f"Morning forecast, {day}")
        + header(TITLE, day, ISSUED, view)
        + KEY
        + confirmation
        + cues_strip(view)
        + body
        + foot(view)
    )
