"""The hit grid and the score strip (story FL1-1c v2). The grid: one row per method, one column per session, each cell
a glyph and its word in the tooltip (inside the 50% band, inside the 90% band, a miss, or no forecast); live days
underlined. The strip: each method's coverage and error over 7, 14 and 30 sessions, with its trend line."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

from .model import Cell, MethodRecord
from .svg import sparkline

PHONE_SESSIONS = 15  # the newest sessions a phone shows; older columns are hidden below 600 px
GLYPHS = {"in50": ("&#10003;", "inside the 50% band"), "in90": ("&#10003;", "inside the 90% band only"),
          "miss": ("&#10007;", "miss: outside the 90% band"), "none": ("&middot;", "no forecast")}  # fmt: skip
GRID_KEY = (
    '<span class="key in50">&#10003;</span> inside the 50% band <span class="key in90">&#10003;</span> inside the 90% '
    'band <span class="key miss">&#10007;</span> miss <span class="key none">&middot;</span> no forecast; '
    "live days underlined"
)


def _kind(cell: Cell) -> str:
    if cell.inside_90 is None:
        return "none"
    return "in50" if cell.inside_50 else "in90" if cell.inside_90 else "miss"


def _cell(cell: Cell, old: bool) -> str:
    kind = _kind(cell)
    glyph, words = GLYPHS[kind]
    classes = " ".join(c for c in (kind, "live" if cell.live else "", "old" if old else "") if c)
    return f'<td class="{classes}" title="{cell.day:%d %b}: {words}">{glyph}</td>'


def _cells(cells: Sequence[Cell]) -> str:
    return "".join(_cell(c, i < len(cells) - PHONE_SESSIONS) for i, c in enumerate(cells))


def _head(cells: Sequence[Cell]) -> str:
    out, month = [], None
    for i, cell in enumerate(cells):
        text = f"{cell.day.day}" if cell.day.month == month else f"{cell.day.day}<br>{cell.day:%b}"
        month = cell.day.month
        old = ' class="old"' if i < len(cells) - PHONE_SESSIONS else ""
        out.append(f"<th{old}>{text}</th>")
    return "".join(out)


def _name(record: MethodRecord) -> str:
    star = ' <span class="star" title="best on history so far">&#9733;</span>' if record.best else ""
    return f'<th class="m">{escape(record.method)}{star}</th>'


def hit_grid(records: Sequence[MethodRecord]) -> str:
    banded = [r for r in records if any(c.inside_90 is not None for c in r.cells)]
    if not banded:
        return ""
    cells = banded[0].cells
    rows = "".join(f"<tr>{_name(r)}{_cells(r.cells)}</tr>" for r in banded)
    return (f'<div class="grid-wrap"><table class="hits"><thead><tr><th class="m"></th>{_head(cells)}</tr></thead>'
            f'<tbody>{rows}</tbody></table></div><p class="key-line">{GRID_KEY}</p>')  # fmt: skip


def _rates(record: MethodRecord, attribute: str) -> str:
    return " &middot; ".join("n/a" if getattr(w, attribute) is None else f"{getattr(w, attribute):.0%}"
                             for w in record.windows)  # fmt: skip


def score_strip(records: Sequence[MethodRecord]) -> str:
    rows = []
    for record in records:
        last = record.windows[-1]
        error = "n/a" if last.error_points is None else f"{last.error_points:,.0f}"
        trend = sparkline(record.rolling_90) if any(v is not None for v in record.rolling_90) else "n/a"
        rows.append(f"<tr>{_name(record)}<td>{_rates(record, 'inside_50')}</td><td>{_rates(record, 'inside_90')}</td>"
                    f'<td class="num">{error}</td><td>{trend}</td></tr>')  # fmt: skip
    head = ("<tr><th>Method</th><th>In 50% band<br>7 &middot; 14 &middot; 30 sessions</th>"
            "<th>In 90% band<br>7 &middot; 14 &middot; 30 sessions</th><th class=\"num\">Avg error<br>30, points</th>"
            "<th>90% band, last 20<br>trend (aim 90%, floor 80%)</th></tr>")  # fmt: skip
    body = "".join(rows)
    return f'<div class="table-wrap"><table class="strip"><thead>{head}</thead><tbody>{body}</tbody></table></div>'
