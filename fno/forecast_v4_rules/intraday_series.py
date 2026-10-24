"""V2's and V3's intraday versions (PROTOCOL_v4.md section 1.1, wording W7; story G7b completion, part f): the sum of
A16's live intraday `RV_s` over the horizon `d+1..d+h`, a separate reported series beside the close-proxy one, never
pooled with it and never a family member. A void session voids the day; a session without its row leaves it
unresolved. The one place for the rule: G8 imports it, as it imports `series.py`."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..constants import V2_RV_5S, V3_RV_20S

INTRADAY_SUFFIX = "/intraday"
INTRADAY_SERIES = {f"{q}{INTRADAY_SUFFIX}": q for q in (V2_RV_5S, V3_RV_20S)}  # series key -> its question
# Wording W3, the owner's choice (unsigned): the series' premium-adjusted baseline is the question's own, fitted on the
# close proxy (option B, recommended, the build's default), or fitted on the intraday measure (option A: no value for
# about two years, so every pair is missing). One place to change when the owner signs.
RATIO_CLOSE_PROXY, RATIO_INTRADAY = "close_proxy", "intraday"
SERIES_RATIO_MEASURE = RATIO_CLOSE_PROXY


def question_of(key: str) -> str:
    """The protocol question whose forecasts, baseline, loss, block and horizon a report key uses."""
    return INTRADAY_SERIES.get(key, key)


def intraday_horizon_sum(
    intraday: Mapping[date, float | None], ahead: Sequence[date]
) -> tuple[float | None, bool] | None:
    """`(sum, void)` over the horizon's sessions, `(None, True)` when any is void, None while a session has no row
    (unresolved). `intraday`: A16's live rows by session (None for a void one)."""
    if any(d not in intraday for d in ahead):
        return None
    values = [intraday[d] for d in ahead]
    return (None, True) if any(v is None for v in values) else (sum(values), False)
