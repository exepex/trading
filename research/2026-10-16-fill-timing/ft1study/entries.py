"""The structures entered on each decision day (PROTOCOL.md section 5): every family at width 200 (100 and 300 as
sensitivity; LC and LP at 0, ATM), built by the repository's own structures at NIFTY's index close at the decision time
from the expiry's chain listed in the panel that day."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from fno.constants import STRUCTURES_BOUGHT_ONLY
from fno.research_engine.structures import Leg, Structure

from .bars import BarBook
from .contracts import MonthlyContracts
from .days import DecisionDay
from .times import Moment

MAIN_WIDTH = 200
SENSITIVITY_WIDTHS = (100, 300)
BOUGHT_ONLY_WIDTH = 0
INDEX_MISSING = "index candle missing at the decision time"


def main_width(code: str) -> int:
    return BOUGHT_ONLY_WIDTH if code in STRUCTURES_BOUGHT_ONLY else MAIN_WIDTH


def widths(code: str) -> tuple[int, ...]:
    return (BOUGHT_ONLY_WIDTH,) if code in STRUCTURES_BOUGHT_ONLY else (MAIN_WIDTH, *SENSITIVITY_WIDTHS)


class IndexLevels:
    """NIFTY's level at a moment: the close of A16b's index candle ending then."""

    def __init__(self, book: BarBook):
        self.book = book

    def level(self, moment: Moment) -> float | None:
        bar = self.book.at(moment.candle_start)
        return bar.close if bar else None


@dataclass(frozen=True)
class Entry:
    day: DecisionDay
    decision: Moment
    family: str
    width: int
    spot: float
    legs: tuple[Leg, ...] | None  # None: a leg is not listed that day (width unavailable)


def build_entries(days: Iterable[DecisionDay], decisions: Sequence, structures: Sequence[Structure],
                  contracts: MonthlyContracts, index: IndexLevels) -> tuple[list[Entry], Counter]:  # fmt: skip
    """Every (day, decision time, family, width) entry, and the days left out per decision time (index missing)."""
    found, left_out = [], Counter()
    for day in days:
        chain = contracts.listed[day.expiry].get(day.day, frozenset())
        for at in decisions:
            decision = Moment(day.day, at)
            spot = index.level(decision)
            if spot is None:
                left_out[(at, INDEX_MISSING)] += 1
                continue
            for structure in structures:
                for width in widths(structure.code):
                    legs = structure.legs(chain, spot, width)
                    found.append(Entry(day, decision, structure.code, width, spot, tuple(legs) if legs else None))
    return found, left_out
