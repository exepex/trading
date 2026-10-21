"""Run 1's work on one cell (protocol sections 6 and 9): fit every candidate on train, choose C11's pair on train,
then on 2024 keep the eligible candidates (calibration bands, no crossing, no input gap over 5%, a successful fit)
and choose the one with the most negative paired QS difference against C0, if negative."""

from __future__ import annotations

from collections.abc import Sequence

from .candidates import C11_POOL, SINGLE, Candidate, Context, combined
from .evaluate import Numbers, numbers, with_features
from .fit import FAILED_NO_ROWS, fit, scaled
from .rows import Row
from .scaling import quantile_score

BAND_90, BAND_50 = (0.87, 0.93), (0.45, 0.55)
GAP_LIMIT = 0.05
NOT_RUN_NO_DATA = "not run: no data for this index"
NOT_RUN_C11 = "not run: fewer than two of C3-C10 improve on C1 on train"


def bands_ok(n: Numbers) -> bool:
    return (n.inside_90 is not None and BAND_90[0] <= n.inside_90 <= BAND_90[1]
            and n.inside_50 is not None and BAND_50[0] <= n.inside_50 <= BAND_50[1])  # fmt: skip


def candidate_for(candidate_id: str) -> Candidate:
    if candidate_id.startswith("C11("):
        first, second = candidate_id[4:-1].split("+")
        return combined(first, second)
    return SINGLE[candidate_id]


def gain_over_c1(candidate: Candidate, theta, c1_theta, rows: Sequence[Row], ctx: Context) -> float | None:
    """Mean of QS(candidate) - QS(C1) on the candidate's own train days (C11's choice, section 6)."""
    data, _ = with_features(candidate, rows, ctx)
    if not data:
        return None
    c1 = SINGLE["C1"]
    gaps = [quantile_score(scaled(candidate, theta, r, x), r.outcome) - quantile_score(scaled(c1, c1_theta, r, [1.0]),
            r.outcome) for r, x in data]  # fmt: skip
    return sum(gaps) / len(gaps)


def _fitted(candidate: Candidate, underlying: str, train: Sequence[Row], ctx: Context) -> dict:
    if candidate.nifty_only and underlying != "NIFTY":
        return {"theta": None, "failed": None, "status": NOT_RUN_NO_DATA}
    data, _ = with_features(candidate, train, ctx)
    result = fit(candidate, data)
    return {"theta": result.theta, "failed": result.failed, "status": "fitted" if not result.failed else "failed"}


def _c11(fits: dict, train: Sequence[Row], ctx: Context) -> Candidate | None:
    c1 = fits["C1"]
    if c1["failed"] or c1["theta"] is None:
        return None
    gains = {}
    for cid in C11_POOL:
        f = fits[cid]
        if f["status"] == "fitted":
            gain = gain_over_c1(SINGLE[cid], f["theta"], c1["theta"], train, ctx)
            if gain is not None and gain < 0:
                gains[cid] = gain
    best = sorted(gains, key=lambda c: (gains[c], c))[:2]
    return combined(*sorted(best, key=C11_POOL.index)) if len(best) == 2 else None


def select_cell(underlying: str, train: Sequence[Row], select: Sequence[Row], ctx: Context) -> dict:
    fits = {cid: _fitted(c, underlying, train, ctx) for cid, c in SINGLE.items()}
    c11 = _c11(fits, train, ctx)
    if c11 is None:
        fits["C11"] = {"theta": None, "failed": None, "status": NOT_RUN_C11}
    else:
        data, _ = with_features(c11, train, ctx)
        result = fit(c11, data)
        fits[c11.id] = {"theta": result.theta, "failed": result.failed,
                        "status": "fitted" if not result.failed else "failed"}  # fmt: skip
    table, eligible = {}, {}
    for cid, f in fits.items():
        entry = dict(f, eligible=False, reason=f["status"])
        if f["status"] == "fitted":
            cand = candidate_for(cid)
            entry["train"] = numbers(cand, f["theta"], train, ctx).as_dict()
            sel = numbers(cand, f["theta"], select, ctx)
            entry["select"] = sel.as_dict()
            entry["reason"] = _ineligible(sel)
            if entry["reason"] is None:
                entry["eligible"] = True
                eligible[cid] = entry["select"]["mean_qs_difference_vs_c0"]
        table[cid] = entry
    winner = winner_of(eligible)
    c0_train, c0_select = numbers(None, None, train, ctx), numbers(None, None, select, ctx)
    return {
        "candidates": table,
        "winner": winner,
        "c0": {"train": c0_train.as_dict(), "select": c0_select.as_dict(), "select_bands_ok": bands_ok(c0_select)},
    }


def winner_of(eligible: dict[str, float | None]) -> str | None:
    """The eligible candidate with the most negative paired difference against C0, if any is negative (section 9)."""
    better = {c: d for c, d in eligible.items() if d is not None and d < 0}
    return min(better, key=lambda c: (better[c], c)) if better else None


def _ineligible(n: Numbers) -> str | None:
    if n.days == 0:
        return FAILED_NO_ROWS
    if n.crossed:
        return "failed: quantiles cross on a select day"
    if n.dropped_share > GAP_LIMIT:
        return f"not decided: {n.dropped_share:.1%} of days miss an input (over 5%)"
    if not bands_ok(n):
        return "outside the calibration bands on 2024"
    return None
