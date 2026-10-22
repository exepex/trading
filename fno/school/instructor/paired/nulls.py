"""The comparison's own checks on fakes (story MS-INS, part d; 325 section 6.2, 327 correction 3): how often a driver
with no edge reaches "watching" (the false-claim rate under shared shocks and overlapping holds), and how many sessions
a planted edge needs to reach it. Both run the real series and status code on simulated road-slots, never on
records."""

import math
import random
from dataclasses import dataclass
from datetime import date, timedelta

from ...constants import RoadCode
from ..contracts import MapStatus, Measure
from .series import paired_series
from .status import paired_row
from .values import RoadSlot, SlotStatus

ROADS = tuple(RoadCode)
FIRST_SESSION = date(2027, 1, 4)


@dataclass(frozen=True)
class Market:
    """A simulated market: each session's shared shock, how much the roads share it, the hold in sessions and the
    spread of a trade's return on risk around its edge."""

    shared: float = 0.6  # correlation of two roads' outcomes on one session
    hold: int = 10  # sessions: each outcome sums the shocks over its hold, so neighbouring sessions overlap
    spread: float = 0.5  # standard deviation of one trade's return on risk


def simulated_slots(seed: int, sessions: int, edge: float, market: Market | None = None):
    """A driver trading every road every session (return on risk: edge plus shared and own noise) against N0."""
    market, draw = market or Market(), random.Random(seed)
    shocks = [draw.gauss(0, 1) for _ in range(sessions + market.hold)]
    days = [FIRST_SESSION + timedelta(days=i) for i in range(sessions)]
    driver, control = {}, {}
    for i, day in enumerate(days):
        common = sum(shocks[i : i + market.hold]) / market.hold**0.5
        for road in ROADS:
            own = draw.gauss(0, 1)
            ror = edge + market.spread * (market.shared**0.5 * common + (1 - market.shared) ** 0.5 * own)
            driver[(day, road)] = RoadSlot(day, road, "D@1", SlotStatus.CLOSED, ror)
            control[(day, road)] = RoadSlot(day, road, "N0@1", SlotStatus.ABSTAINED)
    return driver, control


def share_watching(edge: float, sessions: int, seeds: range, batch: int, market: Market | None = None) -> float:
    """The share of seeded simulations whose paired row against N0 reads "watching" after `sessions` sessions."""
    watching = 0
    for seed in seeds:
        driver, control = simulated_slots(seed, sessions, edge, market)
        series = paired_series(driver, control, set(driver), Measure.PER_OPPORTUNITY)
        watching += (
            paired_row("D@1", "N0@1", Measure.PER_OPPORTUNITY, series, batch, "simulation").status == MapStatus.WATCHING
        )
    return watching / len(seeds)


def wilson_upper(share: float, n: int, z: float = 1.96) -> float:
    """The upper end of the 95% Wilson interval of a share measured on n runs (the orchestrator's gate)."""
    centre = share + z * z / (2 * n)
    spread = z * math.sqrt(share * (1 - share) / n + z * z / (4 * n * n))
    return (centre + spread) / (1 + z * z / n)
