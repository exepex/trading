"""The editions' check block (owner, 23 Oct 2026, "Owner on the evening forecast report" in the conversation log):
per index and in this order, the verdict (the close against both ranges, glyph plus word) or, when there is none,
a red line first saying what is missing and why; the last checked day is then named, never shown as today. The
words are the FL1 builder's text lines' (story FL1-1e): "inside “most likely”: yes/no", "inside “almost
certainly”: yes/no", "verdict: ✓ right / ✗ wrong"; right = inside "almost certainly", the one definition."""

from __future__ import annotations

from datetime import date
from html import escape

from ..page.model import IndexView, PageView
from .blocks import result_card
from .formats import GLYPH, GREEN, RED, WORD, long
from .values import Day

YES_NO = {True: "yes", False: "no"}  # FL1-1e's words; read from plain.py once the builder's branch carries them
VERDICTS = {True: "✓ right", False: "✗ wrong"}
NOT_CHECKED = "today: not checked (no verdict)"
NEXT_MORNING = "the next morning report"
TOMORROW_MORNING = "tomorrow morning's report"
CLOSE_READ = "NSE's close; the official file confirms it in {report}"
CLOSE_OFFICIAL = "NSE's official close"
LAST_CHECKED = "last checked: {day}, {result}"


def morning_report(day: date, next_session: date | None) -> str:
    """ "tomorrow morning's report" only when the next session is the next calendar day; else that weekday's, so a
    Friday never says "tomorrow" for Monday (owner, 23 Oct)."""
    if next_session is None:
        return NEXT_MORNING
    return TOMORROW_MORNING if (next_session - day).days == 1 else f"{next_session:%A}'s morning report"


def report_of(view: PageView) -> str:
    return morning_report(view.day, getattr(view, "next_session", None))


def close_label(d: Day, view: PageView) -> str:
    return CLOSE_READ.format(report=report_of(view)) if d.provisional else CLOSE_OFFICIAL


def check_lines(d: Day, prefix: str, label: str) -> str:
    """The four lines of the verdict: the close, inside each range yes/no, right or wrong."""
    inside_50, inside_90 = d.result == GREEN, d.result != RED
    colour = GREEN if inside_90 else RED
    return (
        f'<ul class="check"><li>{escape(prefix)}: closed <b>{d.close:,.2f}</b> ({escape(label)})</li>'
        f"<li>inside “most likely”: <b>{YES_NO[inside_50]}</b></li>"
        f"<li>inside “almost certainly”: <b>{YES_NO[inside_90]}</b></li>"
        f'<li>verdict: <b class="{colour}">{VERDICTS[inside_90]}</b></li></ul>'
    )


def unchecked_block(index: IndexView, days: list[Day]) -> str:
    """No verdict: the red line first (what is missing and why), then the last checked day, named as such."""
    why = getattr(index, "unchecked", "") or NOT_CHECKED
    last = days[-1] if days else None
    named = (
        f'<p class="line">{LAST_CHECKED.format(day=long(last.day), result=f"{GLYPH[last.result]} {WORD[last.result]}")}'
        "</p>"
        if last
        else ""
    )
    return f'<p class="nocheck">⚠ {escape(why)}</p>{named}'


def evening_verdict(index: IndexView, view: PageView, today: Day | None, days: list[Day]) -> str:
    if today is None:
        return unchecked_block(index, days)
    return check_lines(today, "today", close_label(today, view)) + result_card(today, report_of(view))


def morning_check(index: IndexView, view: PageView, checked: Day | None) -> str:
    """The morning's check of the previous session on NSE's official close, when the model carries one."""
    if checked is None:
        return ""
    return (
        f'<div class="lab">Last session’s check</div>'
        f"{check_lines(checked, long(checked.day), close_label(checked, view))}"
    )
