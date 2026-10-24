"""Run 1's work on one cell (protocol sections 6 and 9): fit every candidate on its own train rows, with each
non-intercept conditioner divided by its train SD (judge 442 SF1, deviation 4); choose C11's pair on train; then on
2024 keep the eligible candidates (calibration bands, no crossing, no input gap over 5% in train or 2024, a fit) and
choose the one with the most negative paired QS difference against C0, if negative."""

from __future__ import annotations

from collections.abc import Sequence

from .candidates import C11_POOL, SINGLE, Candidate, Context, column_scales, combined, standardised
from .evaluate import Numbers, numbers, with_features
from .fit import FAILED_NO_ROWS, fit, scaled
from .rows import Row
from .scaling import quantile_score
from .splits import c9_split

BAND_90, BAND_50 = (0.87, 0.93), (0.45, 0.55)
GAP_LIMIT = 0.05
NOT_RUN_NO_DATA = "not run: no data for this index"
NOT_RUN_C11 = "not run: fewer than two of C3-C10 improve on C1 on train"
FITTED, FAILED = "fitted", "failed"


def bands_ok(n: Numbers) -> bool:
    return (n.inside_90 is not None and BAND_90[0] <= n.inside_90 <= BAND_90[1]
            and n.inside_50 is not None and BAND_50[0] <= n.inside_50 <= BAND_50[1])  # fmt: skip


def candidate_for(candidate_id: str, scales: Sequence[float] = ()) -> Candidate:
    """A candidate by its id, standardised by the train SDs stored with its fit (run 2 rebuilds it the same way)."""
    if candidate_id.startswith("C11("):
        first, second = candidate_id[4:-1].split("+")
        base = combined(first, second)
    else:
        base = SINGLE[candidate_id]
    return standardised(base, scales or ())


def own_train(candidate: Candidate, train: Sequence[Row]) -> list[Row]:
    """The candidate's train period: C8's (and a C11 with C8) starts 2 Jan 2020, when its data does (section 7)."""
    return [r for r in train if candidate.train_from is None or r.day >= candidate.train_from]


def fitted(candidate: Candidate, train: Sequence[Row], ctx: Context) -> tuple[dict, Candidate]:
    """The fit on the candidate's own train rows, in standardised units, and the standardised candidate."""
    raw, _ = with_features(candidate, own_train(candidate, train), ctx)
    scales = () if candidate.two_band else column_scales(raw)
    scaled_candidate = standardised(candidate, scales)
    result = fit(scaled_candidate, with_features(scaled_candidate, own_train(candidate, train), ctx)[0])
    entry = {"theta": result.theta, "failed": result.failed, "scales": scales,
             "status": FITTED if not result.failed else FAILED}  # fmt: skip
    return entry, scaled_candidate


def gain_over_c1(candidate: Candidate, theta, c1_theta, rows: Sequence[Row], ctx: Context) -> float | None:
    """Mean of QS(candidate) - QS(C1) on the candidate's own train days (C11's choice, section 6)."""
    data, _ = with_features(candidate, own_train(candidate, rows), ctx)
    if not data:
        return None
    c1 = SINGLE["C1"]
    gaps = [quantile_score(scaled(candidate, theta, r, x), r.outcome) - quantile_score(scaled(c1, c1_theta, r, [1.0]),
            r.outcome) for r, x in data]  # fmt: skip
    return sum(gaps) / len(gaps)


def _c11(fits: dict, built: dict, train: Sequence[Row], ctx: Context) -> Candidate | None:
    c1 = fits["C1"]
    if c1["status"] != FITTED:
        return None
    gains = {}
    for cid in C11_POOL:
        if fits[cid]["status"] == FITTED:
            gain = gain_over_c1(built[cid], fits[cid]["theta"], c1["theta"], train, ctx)
            if gain is not None and gain < 0:
                gains[cid] = gain
    best = sorted(gains, key=lambda c: (gains[c], c))[:2]
    return combined(*sorted(best, key=C11_POOL.index)) if len(best) == 2 else None


def fit_all(underlying: str, train: Sequence[Row], ctx: Context) -> tuple[dict, dict]:
    fits, built = {}, {}
    for cid, candidate in SINGLE.items():
        if candidate.nifty_only and underlying != "NIFTY":
            fits[cid] = {"theta": None, "failed": None, "scales": (), "status": NOT_RUN_NO_DATA}
            continue
        fits[cid], built[cid] = fitted(candidate, train, ctx)
    c11 = _c11(fits, built, train, ctx)
    if c11 is None:
        fits["C11"] = {"theta": None, "failed": None, "scales": (), "status": NOT_RUN_C11}
    else:
        fits[c11.id], built[c11.id] = fitted(c11, train, ctx)
    return fits, built


def select_cell(underlying: str, train: Sequence[Row], select: Sequence[Row], ctx: Context) -> dict:
    fits, built = fit_all(underlying, train, ctx)
    table, eligible = {}, {}
    for cid, f in fits.items():
        entry = dict(f, eligible=False, reason=f["status"])
        if f["status"] == FITTED:
            cand = built[cid]
            on_train = numbers(cand, f["theta"], own_train(cand, train), ctx)
            sel = numbers(cand, f["theta"], select, ctx)
            entry.update(
                train=on_train.as_dict(), select=sel.as_dict(), reason=_train_gap(on_train) or _ineligible(sel)
            )
            if entry["reason"] is None:
                entry["eligible"] = True
                eligible[cid] = entry["select"]["mean_qs_difference_vs_c0"]
            if cid == "C9":
                entry["split"] = {"train": c9_split(underlying, cand, f["theta"], own_train(cand, train), ctx),
                                  "select": c9_split(underlying, cand, f["theta"], select, ctx)}  # fmt: skip
        table[cid] = entry
    c0_train, c0_select = numbers(None, None, train, ctx), numbers(None, None, select, ctx)
    return {
        "candidates": table,
        "winner": winner_of(eligible),
        "c0": {"train": c0_train.as_dict(), "select": c0_select.as_dict(), "select_bands_ok": bands_ok(c0_select)},
    }


def winner_of(eligible: dict[str, float | None]) -> str | None:
    """The eligible candidate with the most negative paired difference against C0, if any is negative (section 9)."""
    better = {c: d for c, d in eligible.items() if d is not None and d < 0}
    return min(better, key=lambda c: (better[c], c)) if better else None


def _train_gap(n: Numbers) -> str | None:
    """Section 13: an input missing on over 5% of a period's days in a cell, train included, leaves it undecided."""
    if n.dropped_share > GAP_LIMIT:
        return f"not decided: {n.dropped_share:.1%} of train days miss {n.dropped_reason}"
    return None


def _ineligible(n: Numbers) -> str | None:
    if n.days == 0:
        return FAILED_NO_ROWS
    if n.crossed:
        return "failed: quantiles cross on a select day"
    if n.dropped_share > GAP_LIMIT:
        return f"not decided: {n.dropped_share:.1%} of 2024 days miss {n.dropped_reason}"
    if not bands_ok(n):
        return "outside the calibration bands on 2024"
    return None
