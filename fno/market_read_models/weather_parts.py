"""The weather page's parts from M1's records (story P2a): drivers, the recent strip, the red share and the scores.

- **Drivers** (story W3, privacy rule 4): each of v0's inputs that changed since the previous session's record, its
  value in plain words; `push` is the sign of that change (up: riskier). They are ordered by the size of the change
  against the input's own typical (median) change over the last 250 records, never by a model coefficient. The
  scheduled events of the next 5 sessions follow, each riskier. No `reaches` colour, no level, no US cue.
- **Recent, red share, scores:** live records only, as M1 counts them. A score is the mean Brier of the operative
  model's live probabilities against a yardstick's in the same records, over the live days resolved by the session;
  the verdict stays `not_tested` (the frozen test is G8's looks)."""

from __future__ import annotations

import statistics
from datetime import date

from ..constants import V6_BIG_MOVE_1S, V6_BIG_MOVE_5S
from ..forecast_v4_rules.records import LIVE
from ..weather.constants import (
    WEATHER_BASELINE_V0,
    WEATHER_OPERATIVE_MODEL,
    WEATHER_RED_MAX_SHARE,
    WEATHER_RED_SHARE_RECORDS,
    WeatherColour,
)
from .weather_inputs import WeatherInputs

BASE_RATE, OK = "base_rate", "ok"
QUESTIONS = (("V6_1d", V6_BIG_MOVE_1S), ("V6_5d", V6_BIG_MOVE_5S))
HORIZON = {V6_BIG_MOVE_1S: 1, V6_BIG_MOVE_5S: 5}
YARDSTICKS = (("base_rate", BASE_RATE), ("v0_checklist", WEATHER_BASELINE_V0))
RECENT_SESSIONS, SCORE_DAYS_NEEDED = 10, 10
DRIVERS = {  # v0's input -> (the contract's driver, its value in plain words)
    "vix_ratio": ("vix_level", lambda v: f"India VIX at {v:.2f} times its median of the previous 250 sessions"),
    "vix_change5": ("vix_change", lambda v: f"India VIX {'up' if v >= 0 else 'down'} {abs(v):.0%} over 5 sessions"),
    "move5": ("recent_big_moves", lambda v: f"NIFTY's largest daily move in the last 5 sessions: {v:.1%}"),
    "rv10": ("realised_volatility", lambda v: f"NIFTY's realised volatility over 10 sessions: {v:.0%} a year"),
}
EVENTS = {"budget": "Union Budget", "rbi_policy": "RBI policy decision", "election_result": "Election results"}


def is_live(record: dict | None) -> bool:
    return record is not None and record["label"] == LIVE


def figure(record: dict, key: str, question: str) -> float | None:
    entry = record["probabilities"][key][question]
    return entry["value"] if entry["status"] == OK else None


def published_colour(record: dict | None) -> str | None:
    """A live record's colour; None for a back-fill record, a missing one or a live one M1 could not score."""
    if not is_live(record) or record["colour"] == WeatherColour.NOT_SCORED:
        return None
    return record["colour"]


def drivers(inputs: WeatherInputs) -> list[dict]:
    """v0's inputs that changed since the previous session's record, strongest change first, then the events."""
    record, history = inputs.record, [inputs.earlier.get(d) for d in inputs.sessions]
    moved = []
    for name, (driver, words) in DRIVERS.items():
        today, before = _value(record, name), _value(history[-1] if history else None, name)
        if today is None or before is None or today == before:
            continue
        typical = _typical_change([_value(r, name) for r in [*history, record]])
        size = abs(today - before) / typical if typical else abs(today - before)
        push = "riskier" if today > before else "calmer"
        moved.append((size, {"driver": driver, "text": words(today), "push": push}))
    events = [{"driver": "scheduled_event", "text": f"{EVENTS.get(e['type'], e['type'])} on {e['date']}",
               "push": "riskier"} for e in record["drivers"]["events_next_5_sessions"] or []]  # fmt: skip
    return [d for _, d in sorted(moved, key=lambda m: -m[0])] + events


def _value(record: dict | None, name: str) -> float | None:
    entry = (record["drivers"].get("v0_inputs") or {}).get(name) if record else None
    return entry["value"] if entry else None


def _typical_change(series: list[float | None]) -> float | None:
    """The median absolute change between consecutive sessions' values over the last 250 changes."""
    changes = [abs(b - a) for a, b in zip(series, series[1:], strict=False) if a is not None and b is not None]
    return statistics.median(changes[-WEATHER_RED_SHARE_RECORDS:]) if changes else None


def recent(inputs: WeatherInputs) -> list[dict]:
    """The last 10 sessions, the day last: the published colour and whether a 2% move came the next session."""
    records = {**inputs.earlier, inputs.day: inputs.record}
    days = [*inputs.sessions, inputs.day][-RECENT_SESSIONS:]
    moves = inputs.outcomes[1]
    return [{"session": d.isoformat(), "colour": published_colour(records.get(d)), "big_move": moves.get(d)}
            for d in days]  # fmt: skip


def _live_records(inputs: WeatherInputs) -> list[dict]:
    return [r for r in [*(inputs.earlier[d] for d in inputs.sessions if d in inputs.earlier), inputs.record]
            if published_colour(r) is not None]  # fmt: skip


def red_share(inputs: WeatherInputs) -> dict:
    """RED's share of the last 250 live records (the day's included), as M1 counts it; over 15% is over-alarming,
    judged only once 250 live records exist."""
    counted = [r["colour"] for r in _live_records(inputs)][-WEATHER_RED_SHARE_RECORDS:]
    reds = sum(c == WeatherColour.RED for c in counted)
    share = reds / len(counted) if counted else None
    full = len(counted) == WEATHER_RED_SHARE_RECORDS
    return {"sessions": len(counted), "red_sessions": reds, "share": share, "max_share": WEATHER_RED_MAX_SHARE,
            "over_alarming": bool(full and share > WEATHER_RED_MAX_SHARE)}  # fmt: skip


def scores(inputs: WeatherInputs) -> list[dict]:
    live = _live_records(inputs)
    return [_score(live, inputs, label, question, name, yardstick) for name, yardstick in YARDSTICKS
            for label, question in QUESTIONS]  # fmt: skip


def _score(live: list[dict], inputs: WeatherInputs, label: str, question: str, name: str, yardstick: str) -> dict:
    outcomes = inputs.outcomes[HORIZON[question]]
    pairs = [(figure(r, WEATHER_OPERATIVE_MODEL, question), figure(r, yardstick, question),
              outcomes.get(date.fromisoformat(r["day"]))) for r in live]  # fmt: skip
    scored = [(p, b, float(y)) for p, b, y in pairs if p is not None and b is not None and y is not None]
    brier = statistics.fmean((p - y) ** 2 for p, _, y in scored) if scored else None
    base = statistics.fmean((b - y) ** 2 for _, b, y in scored) if scored else None
    return {"question": label, "baseline": name, "n_scored": len(scored), "n_needed": SCORE_DAYS_NEEDED,
            "status": "scoring" if len(scored) >= SCORE_DAYS_NEEDED else "not_enough_data",
            "brier": brier, "brier_baseline": base, "skill": 1 - brier / base if base else None,
            "verdict": "not_tested"}  # fmt: skip
