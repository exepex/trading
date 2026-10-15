"""Story G6: V4's dimensionally checked golden example (calendar IV vs session RV), V5's outcome from the frozen
expiry's final settlement with its source and timestamp, and the session set (A7 regular sessions; muhurat and special
excluded) with the disclosed 2017-26 base rates reproduced from the committed closes."""

from __future__ import annotations

import csv
import json
import math
from datetime import date, datetime
from pathlib import Path

import pytest

from fno.desk.settlement import FinalSettlement
from fno.forecast_v4.sessions import is_scored_session, next_scored_sessions
from fno.forecast_v4.settlement import V5OutcomeError, v5_outcome
from fno.forecast_v4.terms import BIG_MOVE
from fno.forecast_v4.units import implied_vol_session_clock, realised_vol_annualised, v4_outcome
from fno.models import IST
from fno.research_data.calendar import load_session_calendar
from fno.storage.raw_source import NseDailyFoSource

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = json.loads((ROOT / "tests/fixtures/forecast_v4/v4_golden.json").read_text(encoding="utf-8"))
CALENDAR = load_session_calendar(ROOT / "research/data/calendar/nse_sessions.csv")
EXPIRY = date(2026, 11, 24)
SEEN = datetime(2026, 11, 24, 21, 41, tzinfo=IST)


def test_v4_golden_realised_side_is_integrated_variance_times_252_over_5_then_root():
    assert math.fsum(GOLDEN["session_variances"]) == pytest.approx(GOLDEN["integrated_realised_variance"], abs=1e-18)
    assert realised_vol_annualised(GOLDEN["session_variances"]) == pytest.approx(GOLDEN["realised_vol_252"], abs=1e-15)


@pytest.mark.parametrize("case", GOLDEN["cases"], ids=lambda c: c["name"])
def test_v4_golden_implied_side_converts_calendar_time_to_session_time(case):
    iv, days, sessions = GOLDEN["implied_vol_calendar"], case["calendar_days"], case["sessions"]
    assert iv**2 * days / 365 == pytest.approx(case["integrated_implied_variance"], abs=1e-18)
    assert implied_vol_session_clock(iv, days, sessions) == pytest.approx(case["implied_vol_252"], abs=1e-15)
    assert v4_outcome(GOLDEN["session_variances"], iv, days, sessions) is case["outcome"]
    wrong = realised_vol_annualised(GOLDEN["session_variances"]) < iv  # raw calendar IV against session RV
    assert wrong is case["wrong_clock_outcome"]


def test_v4_dimensions_agree_both_sides_integrate_to_the_same_window():
    """Over one window, sigma^2 x sessions / 252 is the window's integrated variance on both sides."""
    case = GOLDEN["cases"][0]
    rv_integrated = realised_vol_annualised(GOLDEN["session_variances"]) ** 2 * 5 / 252
    iv_integrated = implied_vol_session_clock(GOLDEN["implied_vol_calendar"], case["calendar_days"], 5) ** 2 * 5 / 252
    assert rv_integrated == pytest.approx(GOLDEN["integrated_realised_variance"], rel=1e-12)
    assert iv_integrated == pytest.approx(case["integrated_implied_variance"], rel=1e-12)


@pytest.mark.parametrize(
    ("variances", "days", "sessions"),
    [([0.0001] * 4, 7, 5), ([0.0001] * 4 + [math.nan], 7, 5), ([0.0001] * 5, 7, 4), ([0.0001] * 5, 4, 5)],
)
def test_v4_refuses_a_void_session_a_short_expiry_or_fewer_calendar_days_than_sessions(variances, days, sessions):
    with pytest.raises(ValueError):
        v4_outcome(variances, 0.138, days, sessions)


def _final(expiry=EXPIRY, price=22_650.0, source=None) -> FinalSettlement:
    return FinalSettlement("NIFTY", expiry, price, source or NseDailyFoSource.path_for(expiry), "ab" * 32)


def test_v5_outcome_is_strictly_inside_k_plus_minus_p_and_keeps_source_and_timestamp():
    outcome = v5_outcome(22_600.0, 400.0, EXPIRY, _final(), SEEN)
    assert outcome.inside and outcome.level == 22_650.0
    assert (outcome.source, outcome.source_sha256, outcome.first_seen_at) == (_final().source, "ab" * 32, SEEN)
    assert not v5_outcome(22_600.0, 400.0, EXPIRY, _final(price=23_000.0), SEEN).inside  # break-even is not inside
    assert not v5_outcome(22_600.0, 400.0, EXPIRY, _final(price=22_100.0), SEEN).inside


def test_v5_refuses_another_expiry_or_a_later_daily_close():
    later = date(2026, 11, 25)
    with pytest.raises(V5OutcomeError, match="settlement of 2026-11-24"):
        v5_outcome(22_600.0, 400.0, EXPIRY, _final(expiry=later), SEEN)
    with pytest.raises(V5OutcomeError, match="expiry day's F&O file"):
        v5_outcome(22_600.0, 400.0, EXPIRY, _final(source=NseDailyFoSource.path_for(later)), SEEN)


def test_v5_refuses_a_level_first_seen_before_the_expiry_close_or_without_a_time_zone():
    with pytest.raises(V5OutcomeError, match="before the expiry's close"):
        v5_outcome(22_600.0, 400.0, EXPIRY, _final(), datetime(2026, 11, 24, 15, 29, tzinfo=IST))
    with pytest.raises(V5OutcomeError):
        v5_outcome(22_600.0, 400.0, EXPIRY, _final(), datetime(2026, 11, 24, 22, 0))
    with pytest.raises(V5OutcomeError, match="K and P"):
        v5_outcome(22_600.0, 0.0, EXPIRY, _final(), SEEN)


def test_session_set_is_a7_regular_sessions_only():
    assert is_scored_session(CALENDAR, date(2026, 10, 14))
    assert not is_scored_session(CALENDAR, date(2023, 11, 12))  # Diwali muhurat
    assert not is_scored_session(CALENDAR, date(2025, 2, 1))  # Saturday budget session (special)
    assert not is_scored_session(CALENDAR, date(2024, 1, 22))  # weekday holiday
    assert next_scored_sessions(CALENDAR, date(2024, 1, 19), 2) == [date(2024, 1, 23), date(2024, 1, 24)]
    assert next_scored_sessions(CALENDAR, date(2023, 11, 10), 1) == [date(2023, 11, 13)]


def test_disclosed_base_rates_are_reproduced_on_regular_sessions_2017_to_14_oct_2026():
    """Protocol section 8: 100 of 2,409 returns at least 2% (4.15%); 331 of 2,405 five-session windows (13.76%)."""
    with open(ROOT / "research/data/nifty-panel/warmup_closes.csv", encoding="utf-8") as handle:
        rows = [r for r in csv.DictReader(handle) if r["date"] <= "2026-10-14"]
    closes = [float(r["underlying"]) for r in rows if is_scored_session(CALENDAR, date.fromisoformat(r["date"]))]
    assert all((r["session"] == "regular") == is_scored_session(CALENDAR, date.fromisoformat(r["date"])) for r in rows)
    big = [abs(math.log(b / a)) >= BIG_MOVE for a, b in zip(closes, closes[1:])]
    windows = [any(big[i : i + 5]) for i in range(len(big) - 4)]
    assert (len(big), sum(big), round(100 * sum(big) / len(big), 2)) == (2_409, 100, 4.15)
    assert (len(windows), sum(windows), round(100 * sum(windows) / len(windows), 2)) == (2_405, 331, 13.76)
