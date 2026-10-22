"""EDGE1's numbers (protocol sections 10-12): per variant the run-1 G1 inputs, the run-2 test, Holm across both
indices, the nomination rule and the report's risk figures. Every bootstrap is G4's `resampled_means` with a block of
2 trades."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from fno.forecast_scoring.block_bootstrap import resampled_means
from fno.scoreboard.uncertainty import holm

from .trade import Trade

BLOCK, RESAMPLES, ALPHA = 2, 10_000, 0.05
MIN_TESTED, MIN_RUN1 = 30, 20  # run 2's floor for a test; run 1's floor for a G1 pass
TAIL_MULTIPLE = 2.0  # a tail trade loses more than 2 x its own credit


def complete(trades: Sequence[Trade]) -> list[Trade]:
    return [t for t in trades if t.taken and not t.incomplete_exit]


def taken(trades: Sequence[Trade]) -> list[Trade]:
    return [t for t in trades if t.taken]


@dataclass(frozen=True)
class G1Inputs:
    n: int
    mean_gross: float
    sd_gross: float
    mean_cost: float  # charges plus pads per trade
    tail_share: float
    tail_mean_loss: float
    sd_net: float
    per_year: float


def g1_inputs(trades: Sequence[Trade], years: float) -> G1Inputs | None:
    found = complete(trades)
    if len(found) < 2:
        return None
    gross = np.array([t.gross for t in found])
    nets = np.array([t.net for t in found])
    tails = [t.net for t in found if -t.net > TAIL_MULTIPLE * t.credit * t.lot]
    return G1Inputs(len(found), float(gross.mean()), float(gross.std(ddof=1)),
                    float(np.mean([t.charges + t.pads for t in found])), len(tails) / len(found),
                    float(-np.mean(tails)) if tails else 0.0, float(nets.std(ddof=1)), len(found) / years)  # fmt: skip


def one_sided_p(nets: Sequence[float], k: int) -> float:
    """p of mean net > 0: the share of re-centred resampled means at least as far above 0 as the observed mean."""
    if len(nets) < MIN_TESTED:
        return 1.0
    observed = float(np.mean(nets))
    means = resampled_means(nets, k, RESAMPLES, block=BLOCK)
    return (1 + int(np.count_nonzero(means - observed >= observed))) / (RESAMPLES + 1)


def mean_net(trades: Sequence[Trade]) -> float | None:
    return float(np.mean([t.net for t in trades])) if trades else None


def drawdown(trades: Sequence[Trade]) -> float:
    """The largest fall of the cumulative net from a previous high, in exit-day order (0 or negative)."""
    peak, low, total = 0.0, 0.0, 0.0
    for t in sorted(trades, key=lambda t: (t.exit_day, t.cycle.expiry)):
        total += t.net
        peak = max(peak, total)
        low = min(low, total - peak)
    return low


def worst_month(trades: Sequence[Trade]) -> tuple[str, float] | None:
    months: dict[str, float] = {}
    for t in trades:
        key = t.exit_day.strftime("%Y-%m")
        months[key] = months.get(key, 0.0) + t.net
    return min(months.items(), key=lambda kv: kv[1]) if months else None


def holm_family(p_values: dict[str, float]) -> dict[str, bool]:
    """Holm at 0.05 across every variant run 2 tests, both indices in one family."""
    names = sorted(p_values)
    return dict(zip(names, holm([p_values[n] for n in names], ALPHA), strict=True))


def nominated(rows: dict[str, dict], limit: int = 2) -> list[str]:
    """Protocol section 11: Holm-significant, positive at the Rs 2 pad, positive on all trades at both pads, and run 1
    positive; at most `limit`, by p."""
    eligible = [name for name, r in rows.items() if r["holm"] and r["mean_net_pad2"] > 0 and r["all_mean_net"] > 0
                and r["all_mean_net_pad2"] > 0 and r["run1_mean_net"] > 0]  # fmt: skip
    return sorted(eligible, key=lambda n: (rows[n]["p"], n))[:limit]


def finite(value: float | None) -> float | None:
    return None if value is None or not math.isfinite(value) else round(value, 4)
