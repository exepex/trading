"""Which baseline is a date's primary comparison (PROTOCOL_v4.md section 3.2).

A baseline is eligible on a date only when it could be computed from inputs first seen before that date's 15:00 cutoff
with its full minimum history (section 3.2's table). V1's primary is HAR on intraday RV from the first date that model
is eligible, HAR on daily RV before; the switch is one way. Every other question has one primary. When the primary is
not eligible the pair is missing (counted), never filled by another baseline.
"""

from __future__ import annotations

from collections.abc import Set

from ..constants import V1_RV_1S, V4_BASELINE_HAR_DAILY, V4_BASELINE_HAR_INTRADAY
from .terms import PRIMARY_BASELINE


def primary_baseline(question: str, eligible: Set[str], intraday_started: bool) -> str | None:
    """The baseline that date's pair uses, or None (the pair is missing). `intraday_started`: intraday HAR was eligible
    on some earlier date of this question, so daily HAR can no longer stand in."""
    if question == V1_RV_1S:
        if V4_BASELINE_HAR_INTRADAY in eligible:
            return V4_BASELINE_HAR_INTRADAY
        return None if intraday_started or V4_BASELINE_HAR_DAILY not in eligible else V4_BASELINE_HAR_DAILY
    declared = PRIMARY_BASELINE[question]
    return declared if declared in eligible else None
