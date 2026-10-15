"""The study's cells (PROTOCOL.md sections 8 and 11-14): per family, decision time and R, the figures with their
intervals, or "insufficient data" when more than 10% of the eligible days lost the structure to a stale or missing leg,
or "too few days" under 30; the paired 15:00-vs-14:00 difference; and the two flip shares."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import time

from .bootstrap import BLOCKS, mean_interval, ratio_interval
from .figures import MIN_DAYS, THRESHOLDS, TOO_FEW, plain, share_above, splits
from .flips import FlipCounts
from .observe import Observation

INSUFFICIENT = "insufficient data"
LEFT_OUT_SHARE_CAP = 0.10
OK = "ok"


@dataclass(frozen=True)
class CellKey:
    family: str
    width: int
    decision: time
    reaction: int

    @property
    def name(self) -> str:
        return f"{self.family} w{self.width} {self.decision:%H:%M} R{self.reaction}"


def status(observations: Sequence[Observation], eligible_days: int) -> str:
    left_out = sum(o.excluded is not None for o in observations)
    if left_out > LEFT_OUT_SHARE_CAP * eligible_days:
        return INSUFFICIENT
    return TOO_FEW if sum(o.c is not None for o in observations) < MIN_DAYS else OK


def computed(observations: Sequence[Observation]) -> list[Observation]:
    return sorted((o for o in observations if o.c is not None), key=lambda o: o.day)


def main_cell(key: CellKey, observations: Sequence[Observation], eligible_days: int, lot: int) -> dict:
    found = computed(observations)
    head = {"cell": key.name, "family": key.family, "width": key.width,
            "status": status(observations, eligible_days), "eligible_days": eligible_days,
            "n": len(found), "left_out": dict(Counter(o.excluded for o in observations if o.excluded)),
            "e4_snapshot": any(o.e4_snapshot for o in observations)}  # fmt: skip
    if head["status"] != OK:
        return head
    figures = plain(found)
    timed = [o for o in found if o.time_part is not None]
    return head | figures | {
        "mean_abs_c_interval": {b: mean_interval([abs(o.c) for o in found], b, key.name) for b in BLOCKS},
        "share_above": {f"{t:.0%}": share_above(found, t) for t in THRESHOLDS},
        "time_part": {"n": len(timed), "not_computed": len(found) - len(timed),
                      "mean_c": _mean([o.c for o in timed]), "mean_time_part": _mean([o.time_part for o in timed])},
        "rupees": {"lot": lot, "p50_c": figures["p50_c"] * lot, "mean_abs_c": figures["mean_abs_c"] * lot},
        "splits": splits(found),
    }  # fmt: skip


def paired(late: dict, early: dict, late_rows: Sequence[Observation], early_rows: Sequence[Observation],
           family: str) -> dict:  # fmt: skip
    """D = max(C at 15:00, 0) - max(C at 14:00, 0) at R = 60 on the days both exist (positive: 15:00 is worse)."""
    name = f"{family} paired 15:00-14:00 R60"
    if late["status"] != OK or early["status"] != OK:
        return {"cell": name, "status": INSUFFICIENT if INSUFFICIENT in (late["status"], early["status"]) else TOO_FEW}
    by_day = {o.day: o for o in computed(early_rows)}
    days = [(o, by_day[o.day]) for o in computed(late_rows) if o.day in by_day]
    if len(days) < MIN_DAYS:
        return {"cell": name, "status": TOO_FEW, "n": len(days)}
    values = [max(a.c, 0.0) - max(b.c, 0.0) for a, b in days]
    return {"cell": name, "status": OK, "n": len(values), "mean_d": _mean(values),
            "interval": {b: mean_interval(values, b, name) for b in BLOCKS}}  # fmt: skip


def flip_shares(cell: dict, observations: Sequence[Observation]) -> dict:
    """The bad- and good-flip shares with expiry-cluster intervals; never a count of wins, a win rate or a P&L."""
    name = f"{cell['cell']} flips"
    if cell["status"] != OK:
        return {"cell": name, "status": cell["status"]}
    found = computed(observations)
    settled = [o for o in found if o.pnl_decision is not None]
    clusters: dict = defaultdict(FlipCounts)
    for o in settled:
        clusters[o.expiry] = clusters[o.expiry].add(o.pnl_decision, o.pnl_fill)
    counts = list(clusters.values())
    return {"cell": name, "status": OK, "expiries": len(counts), "not_settled": len(found) - len(settled),
            "bad_flip_share": _share(counts, "bad", "wins", f"{name}:bad"),
            "good_flip_share": _share(counts, "good", "losses", f"{name}:good")}  # fmt: skip


def _share(counts: list[FlipCounts], top: str, bottom: str, name: str) -> dict | None:
    tops, bottoms = [getattr(c, top) for c in counts], [getattr(c, bottom) for c in counts]
    if not sum(bottoms):
        return None
    low, high, dropped = ratio_interval(tops, bottoms, name)
    return {"share": sum(tops) / sum(bottoms), "interval": (low, high), "dropped_resamples": dropped}


def _mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None
