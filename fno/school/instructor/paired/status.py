"""A paired series' row (story MS-INS, part d; orchestrator's ruling, 22 Oct 2026): its mean and a one-sided 95%
Student-t lower bound on non-overlapping batch means, counted back from the last session (S6's t table), and its
status: Exploratory below 30 sessions, Watching when the bound is above 0 (not a claim, no licence), Not established
otherwise; with fewer than 2 whole batches there is no bound and the row says so (327 correction 3)."""

import math
import statistics

from ....scoreboard.t_check import t_quantile
from ..contracts import MapStatus, Measure, PairedRow
from ..thresholds import MIN_BATCHES, MIN_SESSIONS
from .series import PairedSeries

TOO_FEW_BATCHES = "too few independent batches"


def batch_bound(values: tuple[float, ...], batch: int) -> float | None:
    """The bound on whole batches counted back from the last session; None below `MIN_BATCHES` batches."""
    k = len(values) // batch
    if k < MIN_BATCHES:
        return None
    kept = values[len(values) - k * batch :]
    means = [sum(kept[i * batch : (i + 1) * batch]) / batch for i in range(k)]
    return statistics.fmean(means) - t_quantile(k - 1) * statistics.stdev(means) / math.sqrt(k)


def status(sessions: int, bound: float | None) -> MapStatus:
    if sessions < MIN_SESSIONS:
        return MapStatus.EXPLORATORY
    return MapStatus.WATCHING if bound is not None and bound > 0 else MapStatus.NOT_ESTABLISHED


def paired_row(driver_id: str, control_id: str, measure: Measure, series: PairedSeries, batch: int,
               rules_sha256: str) -> PairedRow:  # fmt: skip
    n = len(series.days)
    bound = batch_bound(series.values, batch)
    note = TOO_FEW_BATCHES if n >= MIN_SESSIONS and bound is None else ""
    return PairedRow(driver_id, control_id, measure, series.days[0] if n else None, series.days[-1] if n else None, n,
                     series.road_slots, series.driver_abstentions, series.control_abstentions, series.unavailable,
                     series.after_cut, sum(series.values) / n if n else None, bound, batch, status(n, bound),
                     rules_sha256, note)  # fmt: skip
