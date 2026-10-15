"""The plain figures of a set of observations (PROTOCOL.md sections 8 and 10): n, the 10th/50th/90th percentiles of
`C`, the mean of `|C|`, the shares of days with `C` above 5%, 10% and 20% of the risk scale, and the split bands.
Percentiles are numpy's default (linear between the two nearest ranks)."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np

from .observe import Observation

MIN_DAYS = 30
TOO_FEW = "too few days"
THRESHOLDS = (0.05, 0.10, 0.20)
SPLIT_THRESHOLD = 0.10


def share_above(observations: Sequence[Observation], threshold: float) -> float:
    return sum(o.c > threshold * o.risk for o in observations) / len(observations)


def plain(observations: Sequence[Observation]) -> dict:
    values = np.asarray([o.c for o in observations], dtype=float)
    p10, p50, p90 = np.percentile(values, [10, 50, 90])
    return {"n": len(values), "p10_c": float(p10), "p50_c": float(p50), "p90_c": float(p90),
            "mean_abs_c": float(np.abs(values).mean()), "mean_c": float(values.mean())}  # fmt: skip


def split_figures(observations: Sequence[Observation]) -> dict:
    """n, percentiles, the mean of |C| and the 10% share; under 30 days, "too few days" and its n."""
    if len(observations) < MIN_DAYS:
        return {"n": len(observations), "status": TOO_FEW}
    figures = plain(observations)
    figures.pop("mean_c")
    return figures | {"share_above_10pct": share_above(observations, SPLIT_THRESHOLD)}


def _nights(o: Observation) -> str:
    return "3 or more" if o.nights >= 3 else str(o.nights)


def _gap(o: Observation) -> str:
    if o.gap is None:
        return "gap unknown"
    return "below 0.5%" if o.gap < 0.005 else "0.5-1%" if o.gap < 0.01 else "1% and more"


def _vix(o: Observation) -> str:
    if o.vix is None:
        return "VIX unknown"
    return "below 13" if o.vix < 13 else "13-18" if o.vix <= 18 else "above 18"


def _to_expiry(o: Observation) -> str:
    return "8-15" if o.sessions_to_expiry <= 15 else "16-25" if o.sessions_to_expiry <= 25 else "26 and more"


SPLITS: dict[str, Callable[[Observation], str]] = {
    "nights": _nights, "gap band": _gap, "VIX band": _vix, "sessions to expiry": _to_expiry,
}  # fmt: skip
UNKNOWN_BANDS = ("gap unknown", "VIX unknown")  # counted only, never figured


def splits(observations: Sequence[Observation]) -> dict:
    out = {}
    for name, band_of in SPLITS.items():
        bands: dict[str, list[Observation]] = {}
        for o in observations:
            bands.setdefault(band_of(o), []).append(o)
        out[name] = {band: {"n": len(rows)} if band in UNKNOWN_BANDS else split_figures(rows)
                     for band, rows in sorted(bands.items())}  # fmt: skip
    return out
