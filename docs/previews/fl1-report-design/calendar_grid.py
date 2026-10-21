"""This month: right vs wrong, as a calendar grid (Mon-Fri columns, weeks as rows). Each trading day is a rounded
cell with its date number, coloured by the result with its glyph; closed weekdays are grey; the future is blank."""

from datetime import date, timedelta

from linechart import status

GLYPH = {"green": "✓", "amber": "⚠", "red": "✗"}
WORD = {"green": "Correct", "amber": "Close call", "red": "Missed"}


def month_grid(days, issue_day):
    """HTML for the issue day's month. `days` are outcomes with an ISO `iso` date."""
    by_date = {d["iso"]: d for d in days}
    first = issue_day.replace(day=1)
    start = first - timedelta(days=first.weekday())
    counts = {"green": 0, "amber": 0, "red": 0}
    cells, cursor = [], start
    while cursor.month <= issue_day.month and cursor.year == issue_day.year or cursor < first:
        if cursor.weekday() < 5:
            key = cursor.isoformat()
            if cursor.month != issue_day.month:
                cells.append('<div class="cal pad"></div>')
            elif key in by_date:
                st = status(by_date[key])
                counts[st] += 1
                cells.append(f'<div class="cal {st}"><b>{cursor.day}</b><span>{GLYPH[st]}</span></div>')
            elif cursor <= issue_day:
                cells.append(f'<div class="cal off"><b>{cursor.day}</b></div>')
            else:
                cells.append(f'<div class="cal future"><b>{cursor.day}</b></div>')
        cursor += timedelta(days=1)
        if cursor.month != issue_day.month and cursor > first:
            break
    total = sum(counts.values())
    head = "".join(f"<span>{w}</span>" for w in ("Mon", "Tue", "Wed", "Thu", "Fri"))
    big = (f'<div class="counts"><b class="green">✓ Correct {counts["green"]}</b> · <b class="amber">⚠ Close call '
           f'{counts["amber"]}</b> · <b class="red">✗ Missed {counts["red"]}</b> <span>of {total} trading days in '
           f'{issue_day.strftime("%B")}</span></div>')
    return f'{big}<div class="calhead">{head}</div><div class="calgrid">{"".join(cells)}</div>'
