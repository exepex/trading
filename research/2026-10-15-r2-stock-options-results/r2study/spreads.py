"""The snapshot's spread buckets (PROTOCOL.md section 6.2, amendment 1 sections B and D8): moneyness x liquidity
tercile, merged when thin, with each bucket's 75th-percentile half-spread, its tradability and its depth."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .rules import BUCKET_MAX_ONE_SIDED_SHARE, BUCKET_MIN_LEGS, PAD_PERCENTILE

MONEYNESS = ("K0", "1 step", "2-3 steps")
TERCILES = 3


@dataclass(frozen=True)
class QuotedLeg:
    steps: int  # |strike - K0| in steps
    previous_contracts: float  # contracts traded on the session before the snapshot
    bid: float | None
    ask: float | None
    bid_qty: float | None
    ask_qty: float | None
    lot: int


@dataclass(frozen=True)
class Bucket:
    moneyness: str
    terciles: tuple[int, ...]  # the liquidity terciles merged into it (0 = least liquid)
    legs: int
    two_sided: int
    half_spread_p75: float | None
    untradable: bool
    depth: dict


def moneyness(steps: int) -> str:
    return MONEYNESS[min(abs(steps), 2)]


def tercile_bounds(contracts: list[float]) -> tuple[float, float]:
    """The 1/3 and 2/3 quantiles of the quoted legs' previous-session contracts."""
    low, high = np.quantile(np.asarray(contracts, dtype=float), [1 / 3, 2 / 3])
    return float(low), float(high)


def tercile(contracts: float, bounds: tuple[float, float]) -> int:
    return 0 if contracts <= bounds[0] else 1 if contracts <= bounds[1] else 2


def merged_groups(sizes: list[int]) -> list[tuple[int, ...]]:
    """Terciles grouped so each group has BUCKET_MIN_LEGS legs: a thin group merges toward the more liquid neighbour
    (the most liquid one toward the middle), the least liquid thin group first, until none is thin or one is left."""
    groups = [(t,) for t in range(len(sizes))]
    count = lambda g: sum(sizes[t] for t in g)  # noqa: E731
    while len(groups) > 1:
        thin = next((i for i, g in enumerate(groups) if count(g) < BUCKET_MIN_LEGS), None)
        if thin is None:
            break
        other = thin + 1 if thin + 1 < len(groups) else thin - 1
        low, high = sorted((thin, other))
        groups[low : high + 1] = [groups[low] + groups[high]]
    return groups


def two_sided(leg: QuotedLeg) -> bool:
    """Both sides quoted and not crossed (a crossed book is treated as one-sided)."""
    return bool(leg.bid and leg.ask and 0 < leg.bid <= leg.ask)


def half_spread(leg: QuotedLeg) -> float:
    mid = (leg.ask + leg.bid) / 2
    return (leg.ask - leg.bid) / 2 / mid


def depth(legs: list[QuotedLeg]) -> dict:
    """Best quantities in lots, descriptive only (amendment 1 section B)."""
    bids = [leg.bid_qty / leg.lot for leg in legs if leg.bid_qty and leg.lot]
    asks = [leg.ask_qty / leg.lot for leg in legs if leg.ask_qty and leg.lot]
    both = [leg for leg in legs if leg.lot and (leg.bid_qty or 0) >= leg.lot and (leg.ask_qty or 0) >= leg.lot]
    stat = lambda xs, q: float(np.percentile(xs, q)) if xs else None  # noqa: E731
    return {
        "bid_lots_median": stat(bids, 50),
        "bid_lots_p25": stat(bids, 25),
        "ask_lots_median": stat(asks, 50),
        "ask_lots_p25": stat(asks, 25),
        "share_one_lot_both_sides": len(both) / len(legs) if legs else None,
    }


def make_bucket(name: str, terciles: tuple[int, ...], legs: list[QuotedLeg]) -> Bucket:
    quoted = [leg for leg in legs if two_sided(leg)]
    spreads = [half_spread(leg) for leg in quoted]
    one_sided_share = (len(legs) - len(quoted)) / len(legs) if legs else 1.0  # exact at 20%, no 1 - x rounding
    return Bucket(
        moneyness=name,
        terciles=terciles,
        legs=len(legs),
        two_sided=len(quoted),
        half_spread_p75=float(np.percentile(spreads, PAD_PERCENTILE)) if spreads else None,
        untradable=not spreads or one_sided_share > BUCKET_MAX_ONE_SIDED_SHARE,
        depth=depth(legs),
    )


class SpreadModel:
    """Buckets from one snapshot, applied to any leg by its steps from K0 and its previous-session contracts."""

    def __init__(self, legs: list[QuotedLeg]):
        if not legs:
            raise ValueError("no quoted legs: the snapshot is empty")
        self.bounds = tercile_bounds([leg.previous_contracts for leg in legs])
        self.buckets: dict[tuple[str, int], Bucket] = {}
        for name in MONEYNESS:
            own = [leg for leg in legs if moneyness(leg.steps) == name]
            by_tercile = [[leg for leg in own if tercile(leg.previous_contracts, self.bounds) == t] for t in range(3)]
            for group in merged_groups([len(t) for t in by_tercile]):
                bucket = make_bucket(name, group, [leg for t in group for leg in by_tercile[t]])
                for t in group:
                    self.buckets[(name, t)] = bucket

    def bucket(self, steps: int, previous_contracts: float) -> Bucket:
        return self.buckets[(moneyness(steps), tercile(previous_contracts, self.bounds))]

    def distinct(self) -> list[Bucket]:
        seen, out = set(), []
        for bucket in self.buckets.values():
            if id(bucket) not in seen:
                seen.add(id(bucket))
                out.append(bucket)
        return out
