"""A paired series' row (story MS-INS, part d): its mean, a two-sided 90% interval from S2's moving-block bootstrap
over sessions (risk 1 a session, so the ratio is the mean), and its status: Exploratory below 30 sessions, Watching
when the interval's lower end is above 0 (not a claim, no licence), Not established otherwise (327 correction 3)."""

import math

from ....scoreboard.series import DailySeries
from ....scoreboard.uncertainty import resampled_ratios
from ..contracts import MapStatus, Measure, PairedRow
from ..thresholds import INTERVAL_TAIL, MIN_SESSIONS, RESAMPLES, SEED
from .series import PairedSeries


def interval(series: PairedSeries, block: int, resamples: int = RESAMPLES) -> tuple[float, float] | None:
    ones = tuple(1.0 for _ in series.days)
    ratios = resampled_ratios(DailySeries(series.days, series.values, ones), SEED, resamples, block)
    if ratios is None:
        return None
    rank = max(math.ceil(INTERVAL_TAIL / 100 * resamples) - 1, 0)
    return ratios[rank], ratios[resamples - 1 - rank]


def status(sessions: int, low: float | None) -> MapStatus:
    if sessions < MIN_SESSIONS:
        return MapStatus.EXPLORATORY
    return MapStatus.WATCHING if low is not None and low > 0 else MapStatus.NOT_ESTABLISHED


def paired_row(driver_id: str, control_id: str, measure: Measure, series: PairedSeries, block: int, rules_sha256: str,
               resamples: int = RESAMPLES) -> PairedRow:  # fmt: skip
    n = len(series.days)
    mean = sum(series.values) / n if n else None
    bounds = interval(series, block, resamples) if n else None
    low, high = bounds if bounds else (None, None)
    return PairedRow(driver_id, control_id, measure, series.days[0] if n else None, series.days[-1] if n else None, n,
                     series.road_slots, series.driver_abstentions, series.control_abstentions, series.unavailable,
                     series.after_cut, mean, low, high, block, status(n, low), rules_sha256)  # fmt: skip
