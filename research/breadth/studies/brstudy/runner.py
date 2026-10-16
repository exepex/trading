"""Runs BR1a's three studies in their fixed order and writes one JSON result file each.

Order: the panel tables, study 1 (agreement, then the window and the primary), study 2 (the worst year on that
window), study 3 (the single loop on the members of that window and of the worst year)."""

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from . import study1, study2, study3
from .daily import daily_losses, scored_pairs
from .stats import look_counts

PRIMARY_PAIRS = study2.PAIRS[:3]  # the three registered-baseline pairs: study 3's members


def load(path: Path) -> dict:
    table = defaultdict(dict)
    with path.open() as f:
        for r in csv.DictReader(f):
            table[r["underlying"]][r["day"]] = r
    return table


def write(out: Path, name: str, result: dict) -> None:
    (out / f"{name}.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")


def members_of(losses: list[dict]) -> np.ndarray:
    return np.stack([study2.differences(losses, p) for p in PRIMARY_PAIRS])


def run_study3(losses: list[dict], window: dict, primary: str, delta: float, worst: dict) -> dict:
    whole = [r for r in losses if window["first"] <= r["day"] <= window["last"]]
    worst_year = [r for r in whole if r["day"][:4] == worst["year"]]
    populations = {"whole": whole, "worst_year": worst_year}
    results = []
    for rate in study3.RATES:
        looks = look_counts(rate, worst["inflated_variance"], delta)
        claims = {}
        for number, (name, rows) in enumerate(populations.items()):
            paths, _ = study3.population_paths(members_of(rows), np.array([r[primary] for r in rows]), looks[1], number)
            for sign in study3.SIGNS:
                claims[f"{name}/{'+d' if sign > 0 else '-d'}"] = study3.false_claims(sign * paths, looks, rate)
        rolling = study3.rolling_windows(members_of(whole), looks[1], rate, looks)
        results.append({"rate": rate, "looks": list(looks), "false_claim": claims, "rolling_real_windows": rolling})
        if study3.select_rate([results[-1]]) is not None:
            break
    selected = study3.select_rate(results)
    return {"loop": results, "selected_rate": selected, "postponed": selected is None,
            "futility": _futility(populations, primary, delta, results[-1]["looks"]) if selected else None}  # fmt: skip


def _futility(populations: dict, primary: str, delta: float, looks: list[int]) -> dict:
    tried = []
    for threshold in study3.FUTILITY_THRESHOLDS:
        rates = {}
        for number, (name, rows) in enumerate(populations.items()):
            members, losses = members_of(rows), np.array([r[primary] for r in rows])
            paths, loss_paths = study3.population_paths(members, losses, looks[1], number)
            for sign in study3.SIGNS:
                rates[f"{name}/{'+d' if sign > 0 else '-d'}"] = study3.false_futility(
                    sign * paths, loss_paths, looks[0], delta, threshold)  # fmt: skip
        tried.append({"threshold": threshold, "false_futility": rates})
        if all(v <= study3.FUTILITY_LIMIT for v in rates.values()):
            return {"tried": tried, "threshold": threshold}
    return {"tried": tried, "threshold": None, "dropped": True}


def run(panel_csv: Path, legacy_overlap: Path, udiff_overlap: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    agreement = study1.agreement(load(legacy_overlap), load(udiff_overlap))
    first, last = agreement["window"]
    table = {u: {d: r for d, r in rows.items() if first <= d <= last} for u, rows in load(panel_csv).items()}
    scored, excluded = scored_pairs(table)
    losses = daily_losses(scored)
    primary = study1.primary_baseline(scored, losses, (first, last))
    write(out, "study1", {"agreement": agreement, "primary": primary, "excluded_by_year": excluded})
    regime = study2.regime(losses, scored, (first, last))
    write(out, "study2", regime)
    window = {"first": first, "last": last}
    write(out, "study3", run_study3(losses, window, primary["primary"], primary["delta"], regime["worst"]))
