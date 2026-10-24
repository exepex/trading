"""F1's statistics (protocol section 8): mean net per trade with a standard error clustered by expiry week, the
one-sided p from its normal approximation, the G1 bound, Holm across the family, the random-gate control (RC1), and
the report's descriptive figures. Trades are the `trade_row` dicts of `trades.py`."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from datetime import date

from fno.scoreboard.uncertainty import holm

ALPHA, Z90, MIN_CLUSTERS = 0.05, 1.2816, 30
RC1_DRAWS, RC1_SEED = 2000, 20261025


def week_of(row: dict) -> tuple[int, int]:
    iso = date.fromisoformat(row["expiry"]).isocalendar()
    return iso[0], iso[1]


def clustered(rows: Sequence[dict]) -> tuple[float | None, float | None, int]:
    """(mean net, clustered standard error, clusters) of the rows."""
    if not rows:
        return None, None, 0
    mean = sum(r["net"] for r in rows) / len(rows)
    sums: dict[tuple[int, int], float] = {}
    for r in rows:
        sums[week_of(r)] = sums.get(week_of(r), 0.0) + r["net"] - mean
    g = len(sums)
    if g < 2:
        return mean, None, g
    se = math.sqrt(sum(s * s for s in sums.values()) * g / (g - 1)) / len(rows)
    return mean, se, g


def one_sided_p(mean: float | None, se: float | None, clusters: int) -> float:
    if mean is None or not se or clusters < MIN_CLUSTERS:
        return 1.0
    return 0.5 * math.erfc(mean / se / math.sqrt(2))


def g1_bound(mean: float | None, se: float | None) -> float | None:
    return None if mean is None or se is None else mean - Z90 * se


def holm_family(p_values: dict[str, float]) -> dict[str, bool]:
    names = sorted(p_values)
    return dict(zip(names, holm([p_values[n] for n in names], ALPHA), strict=True))


def taken(rows: Sequence[dict]) -> list[dict]:
    return [r for r in rows if r["status"] == "taken"]


def mean_of(rows: Sequence[dict]) -> float | None:
    return sum(r["net"] for r in rows) / len(rows) if rows else None


def random_gate_p(all_rows: Sequence[dict], gated_count: int, gated_mean: float | None) -> float | None:
    """Share of RC1_DRAWS random gates (the same number of the structure's cycles, taken or not) whose taken trades'
    mean net is at least the gated mean."""
    if gated_mean is None or gated_count == 0 or gated_count >= len(all_rows):
        return None
    rng, hits, draws = random.Random(RC1_SEED), 0, 0
    for _ in range(RC1_DRAWS):
        mean = mean_of(taken(rng.sample(list(all_rows), gated_count)))
        if mean is None:
            continue
        draws += 1
        hits += mean >= gated_mean
    return hits / draws if draws else None


def drawdown(rows: Sequence[dict]) -> float:
    peak, low, total = 0.0, 0.0, 0.0
    for r in sorted(rows, key=lambda r: (r["expiry"], r["index"])):
        total += r["net"]
        peak = max(peak, total)
        low = min(low, total - peak)
    return low


def worst_four_weeks(rows: Sequence[dict]) -> float | None:
    """The worst sum of net over 4 consecutive expiry weeks that have trades."""
    weeks: dict[tuple[int, int], float] = {}
    for r in rows:
        weeks[week_of(r)] = weeks.get(week_of(r), 0.0) + r["net"]
    ordered = [weeks[k] for k in sorted(weeks)]
    if len(ordered) < 4:
        return None
    return min(sum(ordered[i : i + 4]) for i in range(len(ordered) - 3))


def by_key(rows: Sequence[dict], key) -> dict[str, dict]:
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(key(r), []).append(r)
    return {k: {"trades": len(v), "mean_net": mean_of(v)} for k, v in sorted(groups.items())}


def sample_plan(sd: float | None, mean: float | None, per_year: float = 50.0) -> dict | None:
    """G3: n = (1.645 x sd / mean)^2 forward trades and the years at `per_year` trades (NIFTY's weekly)."""
    if sd is None or mean is None or mean <= 0:
        return None
    n = math.ceil((1.645 * sd / mean) ** 2)
    return {"trades": n, "years": round(n / per_year, 1)}


def sd_of(rows: Sequence[dict]) -> float | None:
    if len(rows) < 2:
        return None
    m = mean_of(rows)
    return math.sqrt(sum((r["net"] - m) ** 2 for r in rows) / (len(rows) - 1))
