"""Hand-built calendar, official closes and forecasts for the story G4 tests."""

from __future__ import annotations

from datetime import date, timedelta

from fno.constants import BASELINE_BASE_RATE, BOOK1_RULES, FORECAST_QUESTIONS
from fno.forecast.closes_source import OfficialCloses
from fno.forecast.iv30 import AtmIv30
from fno.forecast.targets import trading_days
from fno.forecast_scoring.resolution import OfficialOutcomes
from fno.forecast_scoring.score_inputs import CLOSE_PROXY, ScoredForecast
from fno.research_data.calendar import CsvSessionCalendar

SOURCE = "https://nsearchives.nseindia.com/content/circulars/test.pdf"
CALENDAR = CsvSessionCalendar(f"date,kind,description,source_url\n2025-01-27,holiday,test holiday,{SOURCE}\n")
DAYS = trading_days(CALENDAR, date(2025, 1, 1), date(2025, 6, 30))
FIRST = DAYS[0]  # 1 Jan 2025


def nifty_close(i: int) -> float:
    """Up 0.4% a day on even days, down 0.1% on odd ones: deterministic, never flat."""
    return 23000.0 * (1.004 ** ((i + 1) // 2)) * (0.999 ** (i // 2))


def closes(through: date, missing: tuple[date, ...] = ()) -> OfficialCloses:
    rows = {d: (nifty_close(i), 14.0 + (i % 7)) for i, d in enumerate(DAYS) if d <= through and d not in missing}
    return OfficialCloses("fixture", rows)


def horizon_day(day: date, sessions: int) -> date | None:
    ahead = trading_days(CALENDAR, day + timedelta(days=1), day + timedelta(days=45))
    return ahead[sessions - 1] if len(ahead) >= sessions else None


def outcomes(as_of: date, iv30=None, data_through: date | None = None, missing=()) -> OfficialOutcomes:
    iv30 = iv30 or (lambda day: (True, AtmIv30(30.0, False, (date(2025, 6, 26),))))
    return OfficialOutcomes(closes(data_through or as_of, missing), CALENDAR, as_of, iv30, horizon_day)


def forecast(book: str, day: date, question: str, p: float | None, iv30_status: str = "interpolated") -> ScoredForecast:
    return ScoredForecast(CLOSE_PROXY, book, day, question, p, iv30_status)


def daily_forecasts(days, p_book1: float, p_base: float) -> list[ScoredForecast]:
    return [forecast(book, d, q, p) for d in days for q in FORECAST_QUESTIONS
            for book, p in ((BOOK1_RULES, p_book1), (BASELINE_BASE_RATE, p_base))]  # fmt: skip
