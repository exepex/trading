"""Shared fakes for LR1's tests: a calendar, minimal G4 and G8 report documents, and simple sources."""

import json
from datetime import date

from fno.research_data.calendar import SessionCalendar

SATURDAY = date(2026, 10, 17)
WEEK_DAYS = [date(2026, 10, d) for d in range(12, 17)]


class Calendar(SessionCalendar):
    def __init__(self, closed=()):
        self.closed = set(closed)

    def session_kind(self, day):
        return None if day.weekday() >= 5 or day in self.closed else "regular"

    def calendar_sha256(self):
        return "c" * 64


def misses(missed=0):
    return {"observable": 100, "missed": missed, "big_observable": 5, "big_missed": 0, "input_failures": 0}


def _comparison(scored: int) -> dict:
    return {"forecaster": "weather_vix_v1", "baseline": "base_rate", "scored": scored, "mean_difference": -0.0083,
            "relative_improvement": 0.1756, "misses": misses()}  # fmt: skip


def g8_document(scored: int, as_of: str = "2026-10-17", live: int = 3) -> dict:
    """G8's report since G10: each question's live and close-proxy (back-fill) cohorts."""
    proxy = {
        "scores": {"weather_vix_v1": {"n": scored, "mean_brier": 0.0391664, "calibration": []}, "base_rate": None},
        "comparisons": [_comparison(scored)],
    }
    live_block = {"scores": {}, "comparisons": []}
    if live:
        live_block = {"scores": {"weather_vix_v1": {"n": live, "mean_brier": 0.02, "calibration": []}},
                      "comparisons": [_comparison(live)]}  # fmt: skip
    return {"as_of": as_of, "exploratory": True, "questions": [
        {"question": "v1_rv_next_session", "status": "not enough data yet", "live_forecasts": 0, "cohorts": {}},
        {"question": "v4_rv5_below_weekly_atm_iv", "status": "not started", "live_forecasts": 0, "cohorts": {}},
        {"question": "v6_abs_move_2pct_next_session", "status": "scored", "live_forecasts": live,
         "cohorts": {"close_proxy": proxy, "live": live_block}},
    ]}  # fmt: skip


def legacy_g8_document(scored: int, as_of: str) -> dict:
    """G8's report before G10 (one pooled block; no v4 row was live then), as the committed reports still are."""
    return {"as_of": as_of, "exploratory": True, "questions": [
        {"question": "v4_rv5_below_weekly_atm_iv", "status": "not started", "live_forecasts": 0, "scores": {},
         "comparisons": []},
        {"question": "v6_abs_move_2pct_next_session", "status": "scored", "live_forecasts": 0,
         "scores": {"weather_vix_v1": {"n": scored, "mean_brier": 0.04}, "base_rate": None},
         "comparisons": [_comparison(scored)]},
    ]}  # fmt: skip


def g4_document() -> dict:
    return {"as_of": "2026-10-16", "standing": "Secondary to net profit.", "modes": [], "coverage": {},
            "confirmatory_allowed": False, "unverified_live_days": []}  # fmt: skip


def write_report(folder, day: str, document: dict) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{day}.json").write_text(json.dumps(document))


class Captures:
    def __init__(self, states):
        self.states = states

    def capture(self, day):
        return self.states.get(day)


class Deliveries:
    """T1's `DeliveryLog` read side."""

    def __init__(self, attempts):
        self.by_day = attempts

    def attempts(self, day):
        return self.by_day.get(day, [])

    def write(self, day, metadata):
        raise AssertionError("the post-mortem never writes a delivery")


class Count:
    def __init__(self, n):
        self.n = n

    def count(self):
        return self.n
