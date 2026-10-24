"""G13b's test inputs: G13's synthetic chains, a small NSE calendar, closes with a known shape, and a fake archive of
NSE index-close and F&O files."""

from __future__ import annotations

import math
from datetime import date, timedelta

from fno.forecast_v4_rules.series import DayValue
from fno.price_ranges.build import RangeBuilder
from fno.research_data.calendar import CsvSessionCalendar
from fno.research_data.nifty_panel import DailyFiles
from tests.price_distribution.builders import DAY, RATE

CALENDAR = CsvSessionCalendar(
    "date,kind,description,source_url\n2026-10-20,holiday,Test holiday,https://example.invalid\n"
    "2026-12-25,holiday,Christmas,https://example.invalid\n"
)


def closes(last: date = DAY - timedelta(days=1), n: int = 900, base: float = 22_000.0) -> list[DayValue]:
    """Weekday closes ending at `last` (the calendar's own weekdays), a wiggle so every window has returns."""
    days, current = [], last
    while len(days) < n:
        if current.weekday() < 5:
            days.append(current)
        current -= timedelta(days=1)
    return [DayValue(d, base * math.exp(0.01 * math.sin(i))) for i, d in enumerate(reversed(days))]


def builder(method: str = "c0" * 32) -> RangeBuilder:
    return RangeBuilder(CALENDAR, RATE, method)


def index_close_file(values: dict[str, float]) -> bytes:
    lines = ["Index Name,Index Date,Closing Index Value"] + [f"{n},16-10-2026,{v}" for n, v in values.items()]
    return ("\n".join(lines) + "\n").encode()


def daily_files(files: dict[date, tuple[str, bytes]], label: str = "index-close") -> DailyFiles:
    return DailyFiles(label, label, None, None, lambda day: files.get(day, (f"missing_{day}.csv", None)))
