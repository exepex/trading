"""Story B3 criterion 3 (golden tests): the bootstrap lower bound of a committed set of 60 per-opportunity P&L values,
and the 95th percentile of the C1 random-timing control on fixed small examples, each checked against a separate
short script written here (same seed and convention: protocol section 7, fno/research_engine/statistics.py and
controls.py docstrings) and against the committed number."""

import csv
import math
from pathlib import Path

import numpy as np
import pytest

from fno.research_engine.controls import random_timing_totals
from fno.research_engine.experiment_1 import EXPERIMENT_1
from fno.research_engine.statistics import lower_bound, nearest_rank

GOLDEN = Path(__file__).resolve().parents[1] / "fixtures" / "research_engine" / "golden_pnl_60.csv"
SEED, RESAMPLES, INDEX = 20261012, 10_000, 62
COMMITTED_LOWER_BOUND = -759.42  # Rs per opportunity, committed with the 60 values

SC = [1200.0, -300.0, 450.0, -2500.0, 800.0, 950.0, -120.0, 300.0, -700.0, 1500.0, 60.0, -40.0]
BF = [-400.0, 900.0, -150.0, 1300.0, -600.0, -200.0, 700.0, -900.0, 250.0, -100.0, 400.0, -50.0]
BINARY = ["SC" if i in (0, 2, 4, 5, 7, 9, 10) else None for i in range(12)]  # P4-like: 7 SC, 5 no trade
MIXED = ["SC", "BF", "SC", "BF", "SC", None, "BF", "SC", "BF", None, "SC", None]  # P5-like: 5 SC, 4 BF
COMMITTED_P95 = {"binary": 3930.0, "mixed": 5000.0}


def golden_values():
    with GOLDEN.open() as f:
        return [float(row["pnl"]) for row in csv.DictReader(f)]


def independent_lower_bound(values):
    """Protocol section 7 in plain Python: 10,000 resamples of 60 from one draw, means ascending, index 62."""
    draws = np.random.default_rng(SEED).integers(0, len(values), size=(RESAMPLES, len(values)))
    means = sorted(sum(values[i] for i in row) / len(values) for row in draws.tolist())
    return means[INDEX]


def independent_random_timing_p95(chosen, pnl):
    """Each sequence: a permutation; SC then BF (sorted codes) take consecutive slices; p95 by nearest rank."""
    rng, counts = np.random.default_rng(SEED), {a: chosen.count(a) for a in sorted({a for a in chosen if a})}
    totals = []
    for _ in range(RESAMPLES):
        order, start, total = rng.permutation(len(chosen)).tolist(), 0, 0.0
        for action, count in counts.items():
            total += sum(pnl[action][i] for i in order[start : start + count])
            start += count
        totals.append(total)
    return sorted(totals)[math.ceil(0.95 * RESAMPLES) - 1]


def test_the_bootstrap_lower_bound_matches_the_independent_script_and_the_committed_value():
    values = golden_values()
    assert len(values) == 60
    engine = lower_bound(values, EXPERIMENT_1.stats)
    assert engine == pytest.approx(independent_lower_bound(values), abs=0.01)
    assert engine == pytest.approx(COMMITTED_LOWER_BOUND, abs=0.01)


@pytest.mark.parametrize("name, chosen", [("binary", BINARY), ("mixed", MIXED)])
def test_the_random_timing_95th_percentile_is_exactly_the_committed_value(name, chosen):
    pnl = {"SC": SC, "BF": BF}
    totals = random_timing_totals(chosen, pnl, RESAMPLES, SEED)
    assert nearest_rank(totals, 0.95) == COMMITTED_P95[name] == independent_random_timing_p95(chosen, pnl)


def test_random_timing_keeps_each_actions_count():
    pnl = {"SC": [1.0] * 12, "BF": [1000.0] * 12}  # a sequence's total reveals its counts: 5 SC + 4 BF = 4005
    assert set(random_timing_totals(MIXED, pnl, 200, SEED)) == {4005.0}


def test_the_experiment_uses_the_protocols_terms():
    terms = EXPERIMENT_1.stats
    assert (terms.seed, terms.resamples, terms.lower_bound_index, terms.control_runs) == (
        SEED,
        RESAMPLES,
        INDEX,
        RESAMPLES,
    )
    assert (terms.control_percentile, terms.mc_repeats, terms.tax_rate, terms.loss_cap) == (0.95, 20, 0.312, 10_000.0)
