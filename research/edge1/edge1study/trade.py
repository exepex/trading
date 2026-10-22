"""One variant through one cycle (protocol sections 5-7), built from the engine's own pieces: its structures' legs,
`leg_price`, payoff bounds and `PositionCosts`. The rules are EDGE1's, stricter than experiment 1's simulator:
- entry only if every leg traded on the entry day (`untraded_leg_at_entry`), at the widest width whose worst loss fits
  the cap for the cycle's own lot, with the credit strictly inside the payoff bounds (`bad_prices`);
- exit at the trigger close (SL2, TP50), the planned T21 close, or the final settlement (EXP); never another day;
- a leg untraded at the T21 close takes its settlement proxy and the trade is `incomplete_exit`, kept and flagged."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date

from fno.constants import SIDE_BUY, SIDE_SELL
from fno.costs import settlement_charges_breakdown
from fno.research_data.panel_reader import NiftyPanel
from fno.research_engine.cycle_costs import CycleTerms, PositionCosts
from fno.research_engine.cycles import Cycle
from fno.research_engine.leg_prices import LegPrice, contracts_on, leg_price
from fno.research_engine.structures import Leg, Structure, payoff_bounds, position_value

T21, EXP, SL2, TP50 = "T21", "EXP", "SL2", "TP50"
EXITS = (T21, EXP, SL2, TP50)
STOP_MULTIPLE, TARGET_SHARE = 3.0, 0.5  # SL2: mark >= 3 x credit (a loss of 2 x credit); TP50: mark <= half the credit
TAKEN, NOT_LISTED, UNTRADED = "taken", "missing_strikes", "untraded_leg_at_entry"
BAD, CAP = "bad_prices", "no_trade_cap"
NO_ENTRY, NO_EXIT_PRICE, NO_SETTLEMENT = "no_entry_data", "no_exit_price", "no_settlement"


@dataclass(frozen=True)
class Trade:
    status: str  # TAKEN, or why the cycle was not traded
    cycle: Cycle
    exit_rule: str
    width: float | None = None
    lot: int = 0
    legs: tuple[Leg, ...] = ()
    credit: float = 0.0  # per unit at raw entry closes
    exit_day: date | None = None
    exit_how: str = ""  # trigger, planned, settlement
    incomplete_exit: bool = False
    gross: float = 0.0  # rupees for one lot
    charges: float = 0.0
    pads: float = 0.0
    net: float = 0.0

    @property
    def taken(self) -> bool:
        return self.status == TAKEN


def _prices(panel: NiftyPanel, day: date, expiry: date, legs: Sequence[Leg]) -> list[LegPrice]:
    quotes = contracts_on(panel.options_on(day, expiry))
    return [leg_price(quotes.get(leg.contract), day) for leg in legs]


def _all_traded(prices: Sequence[LegPrice]) -> bool:
    return all(p.price is not None and not p.on_settlement for p in prices)


def open_legs(structure: Structure, panel: NiftyPanel, cycle: Cycle, terms: CycleTerms,
              capped: bool = True) -> tuple[str, float | None, list[Leg], list[float]]:  # fmt: skip
    """(status, width, legs, entry prices) at the widest width that passes, largest first."""
    session = panel.session_on(cycle.entry_day)
    quotes = contracts_on(panel.options_on(cycle.entry_day, cycle.expiry))
    if session is None or session.underlying is None or not quotes:
        return NO_ENTRY, None, [], []
    costs, last = PositionCosts(terms), NOT_LISTED
    for width in terms.widths:
        legs = structure.legs(frozenset(quotes), session.underlying, width)
        if legs is None:
            continue
        prices = [leg_price(quotes.get(leg.contract), cycle.entry_day) for leg in legs]
        if not _all_traded(prices):
            last = UNTRADED
            continue
        entry = [p.price for p in prices]
        lowest, highest = payoff_bounds(legs)
        if not lowest < position_value(legs, entry) < highest:
            last = BAD
            continue
        if capped and costs.max_loss(legs, entry) > terms.cap:
            last = CAP
            continue
        return TAKEN, width, legs, entry
    return last, None, [], []


def _mark(legs: Sequence[Leg], prices: Sequence[LegPrice]) -> float:
    """What buying the position back costs per unit at these closes (positive for a credit structure)."""
    return -position_value(legs, [p.price for p in prices])


def _trigger(legs, credit, panel, cycle, exit_rule, days: Sequence[date]) -> tuple[date, list[float]] | None:
    """The first fully traded day before the T21 exit on which SL2 or TP50 fires, with that day's closes."""
    if exit_rule not in (SL2, TP50):
        return None
    for day in days:
        if not cycle.entry_day < day < cycle.exit_day:
            continue
        prices = _prices(panel, day, cycle.expiry, legs)
        if not _all_traded(prices):
            continue
        mark = _mark(legs, prices)
        stopped = exit_rule == SL2 and mark >= STOP_MULTIPLE * credit
        if stopped or (exit_rule == TP50 and mark <= TARGET_SHARE * credit):
            return day, [p.price for p in prices]
    return None


def _settlement_costs(legs: Sequence[Leg], level: float, terms: CycleTerms) -> float:
    return sum(sum(settlement_charges_breakdown(leg.intrinsic(level), terms.lot, SIDE_SELL if leg.bought else SIDE_BUY,
                                                dict(terms.charges)).values()) for leg in legs)  # fmt: skip


def run_trade(structure: Structure, panel: NiftyPanel, cycle: Cycle, terms: CycleTerms, exit_rule: str,
              days: Sequence[date], settlement: Callable[[date], float | None],
              capped: bool = True) -> Trade:  # fmt: skip
    """`days`: the index's sessions in date order; `settlement(expiry)`: the final settlement price, or None."""
    status, width, legs, entry = open_legs(structure, panel, cycle, terms, capped)
    if status != TAKEN:
        return Trade(status, cycle, exit_rule)
    costs, credit = PositionCosts(terms), -position_value(legs, entry)
    opening = costs.charges(legs, entry, True)
    entry_pads = len(legs) * terms.pad * terms.lot
    if exit_rule == EXP:
        level = settlement(cycle.expiry)
        if level is None:
            return Trade(NO_SETTLEMENT, cycle, exit_rule, width, terms.lot, tuple(legs), credit)
        exit_prices = [leg.intrinsic(level) for leg in legs]
        gross = costs.gross(legs, entry, exit_prices)
        charges = opening + _settlement_costs(legs, level, terms)
        return Trade(TAKEN, cycle, exit_rule, width, terms.lot, tuple(legs), credit, cycle.expiry, "settlement", False,
                     gross, charges, entry_pads, gross - charges - entry_pads)  # fmt: skip
    fired = _trigger(legs, credit, panel, cycle, exit_rule, days)
    if fired is not None:
        exit_day, exit_prices, how, incomplete = fired[0], fired[1], "trigger", False
    else:
        planned = _prices(panel, cycle.exit_day, cycle.expiry, legs)
        if any(p.price is None for p in planned):
            return Trade(NO_EXIT_PRICE, cycle, exit_rule, width, terms.lot, tuple(legs), credit, cycle.exit_day)
        exit_day, exit_prices, how = cycle.exit_day, [p.price for p in planned], "planned"
        incomplete = any(p.on_settlement for p in planned)
    gross = costs.gross(legs, entry, exit_prices)
    charges = opening + costs.charges(legs, exit_prices, False)
    pads = costs.pads(legs)
    return Trade(TAKEN, cycle, exit_rule, width, terms.lot, tuple(legs), credit, exit_day, how, incomplete, gross,
                 charges, pads, gross - charges - pads)  # fmt: skip
