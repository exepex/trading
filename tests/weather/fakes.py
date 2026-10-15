"""Hand-made fixtures for the weather tests (story M1): synthetic sessions from chosen log returns and VIX closes."""

from __future__ import annotations

import math
from datetime import date, timedelta

from fno.forecast_v4_rules.baselines import OK, Value
from fno.weather.checklist_v0 import Row
from fno.weather.day import WeatherDays, WeatherInputs

START = date(2020, 1, 1)


def sessions(count: int) -> list[date]:
    return [START + timedelta(n) for n in range(count)]


def rows_from(returns: list[float], vix: float | list[float | None] = 16.0) -> list[Row]:
    """Closes from 100 by the given log returns (one more row than returns); VIX constant or per row."""
    closes = [100.0]
    for r in returns:
        closes.append(closes[-1] * math.exp(r))
    vixes = vix if isinstance(vix, list) else [vix] * len(closes)
    return [Row(d, c, v) for d, c, v in zip(sessions(len(closes)), closes, vixes, strict=True)]


def days_after(rows: list[Row], n: int):
    """A horizon function: the `n`th row after `d` (None past the last row), as the calendar's 5 sessions."""
    days = [r.day for r in rows]

    def horizon(d: date) -> date | None:
        later = [x for x in days if x > d]
        return later[n - 1] if len(later) >= n else None

    return horizon


def weather_days(rows: list[Row], events=(), horizon=None) -> WeatherDays:
    lines = [f"{r.day},regular,{r.close},{r.vix}" for r in rows]
    return WeatherDays(WeatherInputs(rows, lines, list(events), horizon or days_after(rows, 5), "method"))


def ok(value: float) -> Value:
    return Value(OK, value)


class FakeStore:
    """A RawFileStore double for the private Drive part."""

    def __init__(self, fail: Exception | None = None):
        self.files: dict[str, bytes] = {}
        self.fail = fail

    def put(self, name: str, data: bytes) -> None:
        if self.fail:
            raise self.fail
        self.files[name] = data
