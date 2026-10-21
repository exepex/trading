"""The report in plain words (story FL1-1c v3; owner, 21 Oct 2026, DESK_DECISIONS 194aa8b3): the 3 Slack lines and
the words the picture uses. "Most likely" is the 50% range and "almost certainly" the 90% range; percentages and
method names stay in the details. "Right" means the next-session close fell inside "almost certainly"; the light is
green at 25 or more of the last 30 sessions, amber at 24, red at 23 or fewer (a method right 9 days in 10 falls to 23
or fewer by chance about 3% of the time: exact binomial). Ranges are rounded outward to the nearest 10 points, so
the words never claim a narrower range than the forecast."""

from __future__ import annotations

import math
from datetime import date

from .model import Band, IndexView, PageView

STEP = 10  # points: ranges in words are rounded outward to this
WINDOW, GREEN_FROM, AMBER_AT = 30, 25, 24
LIGHTS = {"green": "🟢", "amber": "🟡", "red": "🔴", "none": "⚪"}
LIGHT_WORDS = {"green": "Good", "amber": "Watch", "red": "Check", "none": "Too few days"}
RESEARCH = "Research only. Not a trade tip."
NORMAL = "✅ All systems normal."
EDITIONS = {"morning": ("Today's forecast", "08:50"), "evening": ("Was today's forecast right?", "20:05")}
RESULTS = {(True, True): "✓ Correct", (False, True): "⚠ Close call", (False, False): "✗ Missed"}  # the designer's words
PROVISIONAL = "NSE's close; the official file confirms it tomorrow"


def day_short(day: date) -> str:
    return f"{day:%a} {day.day} {day:%b}"


def when(ahead: int, target: date, today: date) -> str:
    """`ahead`: regular sessions from `today` to `target` (0: today). "tomorrow" only when the next session is the next
    calendar day; otherwise the day, so a holiday or a weekend never makes "tomorrow" wrong."""
    if ahead == 0:
        return "today"
    if ahead == 1 and (target - today).days == 1:
        return "tomorrow"
    words = "next trading day" if ahead == 1 else f"in {ahead} trading days"
    return f"{words}, {day_short(target)}"


def outward(low: float, high: float) -> tuple[int, int]:
    return math.floor(low / STEP) * STEP, math.ceil(high / STEP) * STEP


def likely(band: Band) -> str:
    low, high = outward(band.q25, band.q75)
    return f"{low:,}–{high:,}"


def certain(band: Band) -> str:
    low, high = outward(band.q05, band.q95)
    return f"{low:,}–{high:,}"


def light(index: IndexView) -> str:
    if index.scored < WINDOW:
        return "none"
    return "green" if index.right >= GREEN_FROM else "amber" if index.right == AMBER_AT else "red"


def record_words(index: IndexView) -> str:
    if index.scored == 0:
        return "no scored days yet"
    tested = f" ({index.backtested} back-tested)" if index.backtested else ""  # judge 434: never passed off as live
    return f"right {index.right} of the last {index.scored} days{tested}"


def result_words(index: IndexView, today: date) -> str:
    """The evening's verdict on today's forecast, or "" when today was not checked."""
    points = index.horizons[0].timeline.points if index.horizons else ()
    last = points[-1] if points else None
    if last is None or last.day != today:
        return ""
    label = f" ({PROVISIONAL})" if last.provisional else ""
    return f"today closed {last.close:,.2f}{label}: {RESULTS[(last.inside_50, last.inside_90)]}"


def index_line(index: IndexView, today: date) -> str:
    result = result_words(index, today)
    parts = [f"*{index.underlying}*", *([result] if result else [])]
    for view in index.today:
        parts.append(f"{view.when}: most likely {likely(view.band)} "
                     f"(almost certainly {certain(view.band)})")  # fmt: skip
    return " · ".join(parts) + f" · {LIGHTS[light(index)]} {record_words(index)}"


def status_line(view: PageView) -> str:
    head = " ".join(f"⚠️ {problem.rstrip('.')}." for problem in view.system) if view.system else NORMAL
    return f"{head} {RESEARCH}"


def slack_lines(view: PageView) -> list[str]:
    """The message's text: the edition's title, one line per index, the morning's confirmations, the status line."""
    title, at = EDITIONS[view.edition]
    return [f"*{title}* ({day_short(view.day)}, {at})", *(index_line(i, view.day) for i in view.indices),
            *view.confirmation, status_line(view)]  # fmt: skip
