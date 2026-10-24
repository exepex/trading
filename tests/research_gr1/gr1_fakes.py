"""Synthetic GR1 inputs: implied ranges with a known shape, outcomes drawn from a known (narrower or wider) law, and a
context whose conditioners the tests set. Seeded, so every test is deterministic."""

from __future__ import annotations

import random
from datetime import date, timedelta
from statistics import NormalDist

from gr1study.candidates import Context
from gr1study.rows import Row
from gr1study.scaling import LEVELS

Z = [NormalDist().inv_cdf(p) for p in LEVELS]


def weekdays(first: date, last: date) -> list[date]:
    days, day = [], first
    while day <= last:
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=1)
    return days


def rows(first: date, last: date, implied_sd: float = 0.01, true_sd: float = 0.008, underlying: str = "NIFTY",
         horizon: str = "N1", seed: int = 7, sd_of=None) -> list[Row]:  # fmt: skip
    """Implied is normal with `implied_sd`; the outcome is normal with `true_sd` (or `sd_of(day)`)."""
    rng = random.Random(seed)
    found = []
    for day in weekdays(first, last):
        sd = sd_of(day) if sd_of else true_sd
        target = day + timedelta(days=1 if day.weekday() < 4 else 3)
        found.append(Row(underlying, day, horizon, target, 22_000.0, tuple(z * implied_sd for z in Z),
                         rng.gauss(0.0, sd)))  # fmt: skip
    return found


def context(**changes) -> Context:
    base = dict(vix={}, previous_session=lambda d: d - timedelta(days=1), events={}, expiries={},
                cue_move=lambda cue, d: None, rv_session={}, implied_variance={})  # fmt: skip
    base.update(changes)
    return Context(**base)


def record(underlying: str, day: date, quantiles, s_ref: float = 100.0, horizon: str = "N1",
           target: date | None = None, status: str = "ok") -> dict:  # fmt: skip
    row = {"forecaster": "implied", "horizon": horizon, "status": status, "s_ref": s_ref,
           "target_day": (target or day + timedelta(days=1)).isoformat()}  # fmt: skip
    row.update({f"lq{round(p * 100):02d}": q for p, q in zip(LEVELS, quantiles, strict=True)})
    return {"underlying": underlying, "day": day.isoformat(), "rows": [row]}
