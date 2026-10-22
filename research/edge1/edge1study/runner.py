"""Every variant of one index through its cycles (protocol sections 3-8), one lot of the cycle's own size.

The periods and the seal (section 3): run 1 is the cycles decided in 2019-2022. A decision day is 30-45 days before
expiry, so its last cycles expire by early February 2023. Run 1 sees the panel only up to RUN1_SEAL, 14 Feb 2023:
nothing later is loaded into it. Run 2 is the cycles decided from 1 Jan 2023 whose expiry is on or before the index's
last data day."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date

from fno.research_data.calendar import SessionCalendar
from fno.research_data.panel_reader import NiftyPanel
from fno.research_engine.cycle_costs import LOSS_CAP, WIDTHS, CycleTerms
from fno.research_engine.cycles import Cycle, monthly_cycles

from .structures import MEASURED, TRADEABLE, structure
from .trade import EXITS, T21, Trade, run_trade

NIFTY, BANKNIFTY = "NIFTY", "BANKNIFTY"
INDICES = (NIFTY, BANKNIFTY)
WIDTHS_BY_INDEX = {NIFTY: WIDTHS, BANKNIFTY: tuple(3 * w for w in WIDTHS)}  # section 5: fixed, never tuned
RUN1_FROM, RUN1_TO, RUN1_SEAL = date(2019, 1, 1), date(2022, 12, 31), date(2023, 2, 14)
RUN2_FROM = date(2023, 1, 1)
RUN1, RUN2 = "run1", "run2"
NO_LOT = "no_lot"
PADS = (1.0, 2.0)  # section 7: the decided pad, and the sensitivity


@dataclass(frozen=True)
class Market:
    index: str
    panel: NiftyPanel
    lots: dict[date, dict[date, int]]  # day -> expiry -> units per lot
    settlement: Callable[[date], float | None]  # expiry -> the final settlement price

    @property
    def days(self) -> list[date]:
        return [s.day for s in self.panel.sessions]


def variants() -> list[tuple[str, str]]:
    """The 12 tradeable (structure, exit) pairs, then the 2 naked measurements (T21 only)."""
    return [(code, rule) for code in TRADEABLE for rule in EXITS] + [(code, T21) for code in MEASURED]


def sealed(panel: NiftyPanel, last: date) -> NiftyPanel:
    """The panel with nothing after `last`: run 1's seal, applied before any cycle or price is read."""
    return NiftyPanel(tuple(s for s in panel.sessions if s.day <= last),
                      {d: q for d, q in panel.options.items() if d <= last},
                      {d: q for d, q in panel.futures.items() if d <= last})  # fmt: skip


def cycles_of(panel: NiftyPanel, calendar: SessionCalendar, first: date, last: date, expiry_by: date) -> list[Cycle]:
    """The engine's monthly cycles decided in [first, last] whose expiry is on or before `expiry_by`."""
    return [c for c in monthly_cycles(panel, calendar) if first <= c.decision_day <= last and c.expiry <= expiry_by]


def lot_of(market: Market, cycle: Cycle) -> int | None:
    return market.lots.get(cycle.entry_day, {}).get(cycle.expiry)


def run_variant(market: Market, cycles: Sequence[Cycle], code: str, exit_rule: str, charges: dict,
                pad: float) -> list[Trade]:  # fmt: skip
    built, trades = structure(code), []
    for cycle in cycles:
        lot = lot_of(market, cycle)
        if lot is None:
            trades.append(Trade(NO_LOT, cycle, exit_rule))
            continue
        terms = CycleTerms(lot, charges, pad, LOSS_CAP, WIDTHS_BY_INDEX[market.index])
        trades.append(run_trade(built, market.panel, cycle, terms, exit_rule, market.days, market.settlement,
                                capped=code in TRADEABLE))  # fmt: skip
    return trades


def variant_name(index: str, code: str, exit_rule: str) -> str:
    return f"{index} {code} {exit_rule}"
