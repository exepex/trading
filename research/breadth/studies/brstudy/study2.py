"""Study 2 (story BR1a): the regime gate.

By calendar year of the study window, for each pair (the three registered-baseline pairs and the planning pair
`cal60` vs `tilt`): the SD and lag-1 of the daily mean difference and the AR(1)-inflated variance. Also each year's
outcome correlation across names and March-April 2020 on its own. The look counts use the largest inflated
variance over every pair and year (the worst year), computed inside study 3's loop at each candidate rate."""

from collections import defaultdict

import numpy as np

from .sizing_tools import sizing
from .stats import inflated_variance, sd_lag1

PAIRS = (("market", "trail60"), ("market", "cal60"), ("trail60", "cal60"), ("cal60", "tilt"))
CRASH = ("2020-03-01", "2020-04-30")


def differences(losses: list[dict], pair: tuple[str, str]) -> np.ndarray:
    """v4's sign: the second's daily loss minus the first's (negative favours the second)."""
    first, second = pair
    return np.array([row[second] - row[first] for row in losses])


def _row(series: np.ndarray) -> dict:
    sd, lag1 = sd_lag1(series)
    return {"days": len(series), "sd": sd, "lag1": lag1, "inflated_variance": inflated_variance(series)}


def outcome_correlation(scored: dict, days: list[str]) -> float:
    names = sorted(scored)
    index = {d: i for i, d in enumerate(days)}
    y = np.full((len(days), len(names)), np.nan)
    for j, u in enumerate(names):
        for day, (value, _) in scored[u].items():
            if day in index:
                y[index[day], j] = value
    return sizing.avg_corr(y)


def regime(losses: list[dict], scored: dict, window: tuple[str, str]) -> dict:
    first, last = window
    rows = [r for r in losses if first <= r["day"] <= last]
    years = defaultdict(list)
    for r in rows:
        years[r["day"][:4]].append(r)
    table = {}
    for year, chosen in sorted(years.items()):
        days = [r["day"] for r in chosen]
        table[year] = {"pairs": {"/".join(p): _row(differences(chosen, p)) for p in PAIRS},
                       "outcome_correlation": outcome_correlation(scored, days)}  # fmt: skip
    crash = [r for r in rows if CRASH[0] <= r["day"] <= CRASH[1]]
    worst = max(((y, p, v["inflated_variance"]) for y, t in table.items() for p, v in t["pairs"].items()),
                key=lambda item: item[2])  # fmt: skip
    return {"window": list(window), "years": table,
            "march_april_2020": {"/".join(p): _row(differences(crash, p)) for p in PAIRS} if crash else None,
            "worst": {"year": worst[0], "pair": worst[1], "inflated_variance": worst[2]}}  # fmt: skip
