"""The spread caveat (PROTOCOL.md section 15), an order of size only: per family, its number of legs times the median
half-spread of A4's valid 15:00 quotes in one distance band (`fno/quotes/report.py`): the 0-1% band, except SC's 2-3%
(its legs sit about 2% and 3% from spot). The spread at the fill times is not measured."""

from __future__ import annotations

from collections.abc import Sequence

from fno.constants import STRUCTURE_SHORT_CONDOR, STRUCTURES, STRUCTURES_BOUGHT_ONLY
from fno.quotes.report import spread_report

NEAR_BAND, CONDOR_BAND = "0-1%", "2-3%"


def legs_of(family: str) -> int:
    if family in STRUCTURES_BOUGHT_ONLY:
        return 1
    return 4 if family in STRUCTURES else 2  # SF, SC, BF have four legs


def spread_caveat(snapshots: Sequence[str], families: Sequence[str]) -> dict:
    """`snapshots`: the CSV texts of A4's canonical Groww snapshots."""
    bands = spread_report(list(snapshots))["bands"]
    out = {"a4_days": len(snapshots), "families": {}}
    for family in families:
        band = CONDOR_BAND if family == STRUCTURE_SHORT_CONDOR else NEAR_BAND
        median = bands[band]["median_half_spread"]
        out["families"][family] = {
            "band": band,
            "legs": legs_of(family),
            "entry_spread_points": None if median is None else legs_of(family) * median,
        }
    return out
