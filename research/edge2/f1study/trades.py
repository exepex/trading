"""One F1 variant through one weekly cycle (protocol sections 6-7), through EDGE1's frozen trade code with its EXP
exit: entry at the closes only if every leg traded, EDGE1's impossible-price and payoff-bound checks, the widest width
whose worst loss fits the Rs 10,000 cap for the cycle's lot, held to expiry and cash-settled with C1's settlement
charges, the entry pad and no exit pad. The structures are centred on the parity forward: it is passed as the
position's "spot"."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from edge1study.lots import UDIFF, circular_lot
from edge1study.trade import EXP, Trade, run_trade

from fno.research_data.panel_reader import NiftyPanel, OptionQuote, SessionClose
from fno.research_engine.cycle_costs import LOSS_CAP, WIDTHS, CycleTerms
from fno.research_engine.cycles import Cycle
from fno.research_engine.structures import ShortCondor, ShortIronFly, Structure

from .cycles import WeeklyCycle
from .gate import YEAR, GateInputs

WIDTHS_BY_INDEX = {"NIFTY": WIDTHS, "FINNIFTY": WIDTHS, "BANKNIFTY": tuple(3 * w for w in WIDTHS),
                   "MIDCPNIFTY": tuple(w / 2 for w in WIDTHS)}  # section 6: fixed, never tuned  # fmt: skip
STRUCTURES = ("WF", "WC")
NO_LOT = "no_lot"


@dataclass(frozen=True)
class CycleInputs:
    cycle: WeeklyCycle
    quotes: tuple[OptionQuote, ...]  # the entry day's options of the cycle's expiry
    lot: int | None
    gate: GateInputs
    settlement: float | None  # the expiry day's index close


def structure_for(code: str, inputs: CycleInputs) -> Structure:
    if code == "WF":
        return ShortIronFly()
    return ShortCondor(offset=inputs.gate.sigma_iv * (inputs.cycle.sessions / YEAR) ** 0.5)


def lot_of(index: str, rows_lots: Mapping[date, int], source: str, expiry: date,
           schedule: Callable[[str, date], int] = circular_lot) -> int | None:  # fmt: skip
    """UDiFF's board lot of the expiry; else the circular schedule (EDGE1's, extended for the held-out indices)."""
    if source == UDIFF:
        return rows_lots.get(expiry)
    return schedule(index, expiry)


def run_cycle(code: str, inputs: CycleInputs, charges: Mapping[str, float], pad: float,
              charges_on=None) -> Trade:  # fmt: skip
    """`inputs.gate` must be ok and `inputs.lot` set (the caller skips the cycle otherwise)."""
    c = inputs.cycle
    entry = c.entry_day
    panel = NiftyPanel((SessionClose(entry, "regular", inputs.gate.forward, None),), {entry: inputs.quotes}, {})
    cycle = Cycle(c.expiry, entry, entry, c.expiry)
    terms = CycleTerms(inputs.lot, dict(charges), pad, LOSS_CAP, WIDTHS_BY_INDEX[c.index])
    return run_trade(structure_for(code, inputs), panel, cycle, terms, EXP, [entry, c.expiry],
                     lambda _expiry: inputs.settlement, capped=True, charges_on=charges_on)  # fmt: skip


def trade_row(code: str, inputs: CycleInputs, trade: Trade) -> dict:
    c, g = inputs.cycle, inputs.gate
    return {"index": c.index, "structure": code, "expiry": c.expiry.isoformat(), "entry": c.entry_day.isoformat(),
            "sessions": c.sessions, "ratio": g.ratio, "sigma_iv": g.sigma_iv, "sigma_rv": g.sigma_rv,
            "status": trade.status, "width": trade.width, "lot": inputs.lot, "credit": trade.credit,
            "gross": trade.gross, "charges": trade.charges, "pads": trade.pads, "net": trade.net}  # fmt: skip


def run_structure(code: str, cycles: Sequence[CycleInputs], charges, pad: float, charges_on=None) -> list[dict]:
    return [trade_row(code, inputs, run_cycle(code, inputs, charges, pad, charges_on)) for inputs in cycles]
