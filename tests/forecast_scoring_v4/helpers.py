"""Shared builders for the G8 tests: real regular-session closes from the committed warmup file (hand-rebuilt V6b
outcomes, the test's own reference) and a synthetic window with a chosen count of 2% days."""

from __future__ import annotations

import csv
import math
from datetime import date, timedelta
from pathlib import Path

from fno.forecast_scoring.v4.freeze_check import FreezeCheck
from fno.forecast_scoring.v4.inputs import ForecastValue, Outcome
from fno.forecast_scoring.v4.reconcile import AiSlotDays
from fno.forecast_scoring.v4.records import NoRegistrations

WARMUP = Path(__file__).resolve().parents[2] / "research" / "data" / "nifty-panel" / "warmup_closes.csv"


def regular_closes(start: date, end: date) -> list[tuple[date, float, float]]:
    with WARMUP.open(encoding="utf-8", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["session"] == "regular"]
    found = [(date.fromisoformat(r["date"]), float(r["underlying"]), float(r["vix"])) for r in rows]
    return [row for row in found if start <= row[0] <= end]


def v6b_outcomes(sessions) -> dict[date, Outcome]:
    """By hand: any of the next 5 regular close-to-close log returns has abs >= 0.02; the first session's VIX and
    return are the regime inputs. The last 5 days are unresolved (no entry)."""
    returns = [math.log(sessions[i + 1][1] / sessions[i][1]) for i in range(len(sessions) - 1)]
    out = {}
    for i in range(len(sessions) - 5):
        window = returns[i : i + 5]
        out[sessions[i][0]] = Outcome(any(abs(r) >= 0.02 for r in window), False, sessions[i + 1][2], window[0])
    return out


def values(pairs: dict[date, float | None], live: bool = False) -> dict[date, ForecastValue]:
    return {day: ForecastValue(v, live) for day, v in pairs.items()}


def synthetic_window(n: int, big_days: int, start: date = date(2025, 1, 1)):
    """n probability outcomes with exactly `big_days` first-session returns of 3% (else 0.5%), VIX 15, alternating
    events; returns (days, outcomes)."""
    days = [start + timedelta(days=i) for i in range(n)]
    outcomes = {d: Outcome(i % 3 == 0, False, 15.0, 0.03 if i < big_days else 0.005) for i, d in enumerate(days)}
    return days, outcomes


def settled_slot_days():
    """A look's reconciliation with nothing to settle: no registered AI slot."""
    return AiSlotDays(None, NoRegistrations(), lambda first, last: [])


def intact() -> FreezeCheck:
    """The freeze check of a look that holds (story G6 freeze, criterion 4: the check is a required argument)."""
    return FreezeCheck()
