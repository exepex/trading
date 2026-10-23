"""The editions' check block (owner, 23 Oct 2026, "Owner on the evening forecast report" in the conversation log):
per index and in this order, the verdict (the close against both ranges, glyph plus word) or, when there is none,
a red line first saying what is missing and why; the last checked day is then named, never shown as today. The
words are the FL1 builder's text lines' (story FL1-1e, `plain.py`, one source): "inside “most likely”: yes/no",
"inside “almost certainly”: yes/no", "verdict: ✓ right / ✗ wrong"; right = inside "almost certainly"."""

from __future__ import annotations

from html import escape

from ..page.model import IndexView, PageView
from ..page.plain import OFFICIAL, PROVISIONAL, UNCHECKED, VERDICTS, YES_NO, morning_report
from .blocks import result_card
from .formats import GLYPH, GREEN, RED, WORD, long
from .values import Day

# The words are plain.py's (the Slack text's), one source; these three have no text-line twin
NOT_CHECKED = "today: not checked (no verdict)"
NOT_CONFIRMED = "NSE's close; the official file has not confirmed it yet"
LAST_CHECKED = "last checked: {day}, {result}"


def report_of(view: PageView) -> str:
    return morning_report(view.day, view.next_session)


def close_label(d: Day, view: PageView) -> str:
    return PROVISIONAL.format(report=report_of(view)) if d.provisional else OFFICIAL


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


def unchecked_block(index: IndexView, view: PageView, days: list[Day]) -> str:
    """No verdict: the red line first (what is missing and why, the text line's sentence), then the last checked
    day, named as such."""
    why = UNCHECKED[index.unchecked].format(report=report_of(view)) if index.unchecked else NOT_CHECKED
    last = days[-1] if days else None
    named = (
        f'<p class="line">{LAST_CHECKED.format(day=long(last.day), result=f"{GLYPH[last.result]} {WORD[last.result]}")}'
        "</p>"
        if last
        else ""
    )
    return f'<p class="nocheck">⚠ {escape(why)}</p>{named}'


def day_word(d: Day, view: PageView) -> str:
    """ "today" only for the page's own day; a past day is always named (orchestrator, 23 Oct)."""
    return "today" if d.day == view.day else long(d.day)


def evening_verdict(index: IndexView, view: PageView, today: Day | None, days: list[Day]) -> str:
    if today is None:
        return unchecked_block(index, view, days)
    return check_lines(today, day_word(today, view), close_label(today, view)) + result_card(today, report_of(view))


def morning_check(index: IndexView, view: PageView, checked: Day | None) -> str:
    """The morning's check of the previous session on NSE's official close, when the model carries one."""
    if checked is None:
        return ""
    label = NOT_CONFIRMED if checked.provisional else OFFICIAL  # judge 538 F4: never "tomorrow" here
    return f'<div class="lab">Last session’s check</div>{check_lines(checked, long(checked.day), label)}'
