"""Each weekly cycle's inputs (protocol sections 3-5): the entry day's options of the cycle's expiry, the index close
(spot), the gate inputs, the lot, and the settlement (the expiry day's index close), each point in time. A cycle that
cannot be traded by any variant is a skip with its reason, counted in the report."""

from __future__ import annotations

from bisect import bisect_left
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from edge1study.day_files import DayRows
from edge1study.lots import circular_lot

from .cycles import TAKEN_CYCLE, WeeklyCycle
from .gate import gate_inputs
from .trades import NO_LOT, CycleInputs, lot_of

NO_SPOT, NO_SETTLEMENT, NO_GATE = "no_index_close", "no_settlement", "no_gate_input"
SETTLE_TOLERANCE = 0.0005  # the expiry future's settlement within 0.05% of the index close


@dataclass(frozen=True)
class Skip:
    cycle: WeeklyCycle
    reason: str


@dataclass(frozen=True)
class IndexCloses:
    days: tuple[date, ...]  # ascending
    values: tuple[float, ...]

    @classmethod
    def of(cls, closes: Mapping[date, float]) -> IndexCloses:
        days = tuple(sorted(closes))
        return cls(days, tuple(closes[d] for d in days))

    def on(self, day: date) -> float | None:
        i = bisect_left(self.days, day)
        return self.values[i] if i < len(self.days) and self.days[i] == day else None

    def before(self, day: date) -> list[float]:
        return list(self.values[: bisect_left(self.days, day)])


def settlement_check(rows: DayRows | None, expiry: date, level: float) -> bool | None:
    """True/False when a future of that expiry settles on the day (agrees within tolerance), else None."""
    future = next((f for f in rows.futures if f.expiry == expiry and f.settle > 0), None) if rows else None
    return None if future is None else abs(future.settle / level - 1) <= SETTLE_TOLERANCE


Found = tuple[list[CycleInputs], list[Skip], list]


def cycle_inputs(cycles: Sequence[WeeklyCycle], rows: Sequence[DayRows], closes: IndexCloses,
                 schedule: Callable[[str, date], int] = circular_lot) -> Found:  # fmt: skip
    """(tradeable cycles, skips, settlement checks as (expiry, agrees))."""
    by_day = {r.day: r for r in rows}
    found, skips, checks = [], [], []
    for c in cycles:
        if c.status != TAKEN_CYCLE:
            skips.append(Skip(c, c.status))
            continue
        entry_rows, spot, level = by_day[c.entry_day], closes.on(c.entry_day), closes.on(c.expiry)
        if spot is None:
            skips.append(Skip(c, NO_SPOT))
            continue
        if level is None:
            skips.append(Skip(c, NO_SETTLEMENT))
            continue
        quotes = tuple(q for q in entry_rows.options if q.expiry == c.expiry)
        gate = gate_inputs(quotes, c.expiry, spot, c.sessions, closes.before(c.entry_day))
        if gate.status != "ok":
            skips.append(Skip(c, f"{NO_GATE}:{gate.status}"))
            continue
        lot = lot_of(c.index, entry_rows.lots, entry_rows.source, c.expiry, schedule)
        if not lot:
            skips.append(Skip(c, NO_LOT))
            continue
        agrees = settlement_check(by_day.get(c.expiry), c.expiry, level)
        if agrees is not None:
            checks.append((c.expiry.isoformat(), agrees))
        found.append(CycleInputs(c, quotes, lot, gate, level))
    return found, skips, checks
