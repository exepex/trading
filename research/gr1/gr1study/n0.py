"""N0 at 09:15 against N1 at 15:45 on the same target close (protocol section 11; NIFTY only, 2020 on). N0-A moves the
N1 range issued at d-1's close to d's 09:15 price: centre at the 09:15 price, implied's deviations from its median
scaled by sqrt(0.607), the variance share left at 09:15. N0-B adds one fitted scale; N0-C conditions that scale on the
overnight gap and the S&P 500 move known at 09:15. A measurement: no Holm, no "sharper"."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from datetime import date

import numpy as np

from fno.forecast_scoring.block_bootstrap import resampled_means
from fno.price_ranges.scores import comparison_seed

from .candidates import Candidate, Context
from .evaluate import numbers, with_features
from .fit import fit, scaled
from .periods import SELECT, TRAIN, sealed
from .rows import Row
from .scaling import MEDIAN, OUTER, width_points
from .selection import bands_ok

REMAINING_SHARE = 1 - 0.393  # G13b's measured overnight share (exposed: measured on 2020-2025)
N0 = "N0"


def n0_pairs(n1_rows: Sequence[Row], opens: dict[date, float], final_open: bool) -> list[tuple[Row, Row]]:
    """(N0-A row, the N1 row of the same target), sealed by the N0 issue day (the target day itself)."""
    pairs = []
    for n1 in n1_rows:
        if n1.underlying != "NIFTY" or n1.horizon != "N1" or n1.target_day not in opens:
            continue
        open_ = opens[n1.target_day]
        m, root = n1.quantiles[MEDIAN], math.sqrt(REMAINING_SHARE)
        outcome = n1.outcome + math.log(n1.s_ref / open_)  # ln(close / 09:15 price)
        n0 = Row("NIFTY", n1.target_day, N0, n1.target_day, open_, tuple(root * (q - m) for q in n1.quantiles), outcome)
        pairs.append((n1.target_day, (n0, n1)))
    return [pair for _, pair in sealed(pairs, final_open)]


def n0_candidates(gaps: dict[date, float], sp500_open: Callable[[date], float | None]) -> dict[str, Candidate]:
    def conditioned(row: Row, ctx: Context) -> list[float] | None:
        move = sp500_open(row.day)
        return None if move is None or row.day not in gaps else [1.0, abs(gaps[row.day]), move]

    return {"N0-B": Candidate("N0-B", lambda row, ctx: [1.0]), "N0-C": Candidate("N0-C", conditioned)}


def width_ratio(pairs: Sequence[tuple[Row, Row]], candidate: Candidate | None, theta, ctx: Context, key: str) -> dict:
    """Mean of N0's 90% width over N1's on the same days, with a block-bootstrap 95% interval."""
    ratios = []
    for n0, n1 in pairs:
        x = None if candidate is None else candidate.features(n0, ctx)
        if candidate is not None and x is None:
            continue
        q = n0.quantiles if candidate is None else scaled(candidate, theta, n0, x)
        ratios.append(width_points(q, n0.s_ref, OUTER) / width_points(n1.quantiles, n1.s_ref, OUTER))
    if len(ratios) < 40:
        return {"days": len(ratios), "mean_ratio": float(np.mean(ratios)) if ratios else None, "interval_95": None}
    means = resampled_means(ratios, comparison_seed("GR1", N0, key))
    low, high = np.percentile(means, (2.5, 97.5))
    return {"days": len(ratios), "mean_ratio": float(np.mean(ratios)), "interval_95": (float(low), float(high))}


def n0_study(pairs_by_period: dict[str, list], ctx: Context, candidates: dict[str, Candidate]) -> dict:
    train = [n0 for n0, _ in pairs_by_period[TRAIN]]
    out = {"variants": {}, "winner": None}
    better = {}
    for cid, cand in candidates.items():
        result = fit(cand, with_features(cand, train, ctx)[0])
        sel = numbers(cand, result.theta, [n0 for n0, _ in pairs_by_period[SELECT]], ctx) if not result.failed else None
        out["variants"][cid] = {"theta": result.theta, "failed": result.failed,
                                "select": sel.as_dict() if sel else None}  # fmt: skip
        if sel and not sel.crossed and bands_ok(sel) and sel.differences and sum(sel.differences) < 0:
            better[cid] = sum(sel.differences) / len(sel.differences)
    out["winner"] = min(better, key=lambda c: (better[c], c)) if better else "N0-A"
    return out


def n0_report(pairs: Sequence[tuple[Row, Row]], study: dict, ctx: Context, candidates: dict, label: str) -> dict:
    """All three variants and N1 on the same target days of one period."""
    n0_rows, n1_rows = [p[0] for p in pairs], [p[1] for p in pairs]
    report = {"N1": numbers(None, None, n1_rows, ctx).as_dict(), "N0-A": numbers(None, None, n0_rows, ctx).as_dict(),
              "ratio_N0-A": width_ratio(pairs, None, None, ctx, f"{label}:N0-A")}  # fmt: skip
    for cid, cand in candidates.items():
        theta = study["variants"][cid]["theta"]
        if study["variants"][cid]["failed"] or theta is None:
            continue
        report[cid] = numbers(cand, theta, n0_rows, ctx).as_dict()
        report[f"ratio_{cid}"] = width_ratio(pairs, cand, theta, ctx, f"{label}:{cid}")
    return report
