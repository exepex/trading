"""F6's signals, trades and futures costs (protocol sections 3-5). A signal from day t's file trades from session
t+1's open to the close of session t+h, on the NIFTY future with the nearest expiry on or after the exit session."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date

from edge1study.lots import circular_lot

from .data import Session

SIGNALS, HORIZONS = ("FD", "FL", "CD"), {"H1": 1, "H5": 5}
LEVEL_WINDOW = 20
CRORE = 1e7
NO_SIGNAL, NO_PRICE, FLAT, TAKEN = "no_signal", "no_price", "flat_signal", "taken"


@dataclass(frozen=True)
class FuturesRates:
    """The school probe's checked futures rates (protocol section 5); `stt_sell_pct` is replaced by date in the
    historical-STT run."""

    stt_sell_pct: float = 0.05
    nse_per_crore: float = 183.0
    sebi_per_crore: float = 10.0
    stamp_buy_pct: float = 0.002
    brokerage_per_order: float = 20.0
    gst_pct: float = 18.0


HISTORICAL_STT = ((date(2023, 4, 1), 0.0125), (date(2024, 10, 1), 0.02), (date(2026, 4, 1), 0.05))  # before: 0.01


def stt_on(day: date) -> float:
    rate = 0.01
    for start, value in HISTORICAL_STT:
        if day >= start:
            rate = value
    return rate


def order_charges(price: float, units: int, buying: bool, rates: FuturesRates) -> float:
    notional = price * units
    nse, sebi = notional * rates.nse_per_crore / CRORE, notional * rates.sebi_per_crore / CRORE
    tax = notional * (rates.stamp_buy_pct if buying else rates.stt_sell_pct) / 100
    gst = (rates.brokerage_per_order + nse + sebi) * rates.gst_pct / 100
    return tax + nse + sebi + rates.brokerage_per_order + gst


def side_of(signal: str, sessions: Sequence[Session], i: int) -> int | None:
    """+1 long, -1 short, 0 flat, None without the inputs; from day i's file and earlier only."""
    if signal == "FL":
        nets = [s.fii_net for s in sessions[max(0, i - LEVEL_WINDOW + 1) : i + 1]]
        if len(nets) < LEVEL_WINDOW or any(n is None for n in nets):
            return None
        level = nets[-1] - sum(nets) / LEVEL_WINDOW
        return (level > 0) - (level < 0)
    field = "fii_net" if signal == "FD" else "client_net"
    today, before = getattr(sessions[i], field), getattr(sessions[i - 1], field) if i > 0 else None
    if today is None or before is None:
        return None
    change = today - before
    sign = (change > 0) - (change < 0)
    return -sign if signal == "CD" else sign


def contract(entry: Session, exit_: Session):
    """(entry bar, exit bar) of the nearest expiry on or after the exit session, listed on both days."""
    for bar in entry.futures:
        if bar.expiry < exit_.day:
            continue
        out = next((b for b in exit_.futures if b.expiry == bar.expiry), None)
        return (bar, out) if out is not None else (None, None)
    return None, None


def trade(signal: str, horizon: str, sessions: Sequence[Session], i: int, rates: FuturesRates, pad: float,
          stt: Callable[[date], float] | None = None) -> dict | None:  # fmt: skip
    """The trade of day i's signal, or None when its exit session is beyond the data."""
    h = HORIZONS[horizon]
    if i + h >= len(sessions):
        return None
    entry, exit_ = sessions[i + 1], sessions[i + h]
    row = {"signal_day": sessions[i].day.isoformat(), "entry": entry.day.isoformat(), "exit": exit_.day.isoformat()}
    side = side_of(signal, sessions, i)
    if side is None or side == 0:
        return {**row, "status": NO_SIGNAL if side is None else FLAT, "side": side, "net": 0.0}
    first, last = contract(entry, exit_)
    if first is None or first.open <= 0 or last.close <= 0:
        return {**row, "status": NO_PRICE, "side": side, "net": 0.0}
    lot = first.lot or circular_lot("NIFTY", first.expiry)
    buy_price, sell_price = (first.open, last.close) if side > 0 else (last.close, first.open)
    sell_day = exit_.day if side > 0 else entry.day
    used = rates if stt is None else FuturesRates(stt_sell_pct=stt(sell_day))
    charges = order_charges(buy_price, lot, True, used) + order_charges(sell_price, lot, False, used)
    gross = side * (last.close - first.open) * lot
    pads = 2 * pad * lot
    return {**row, "status": TAKEN, "side": side, "lot": lot, "gross": gross, "charges": charges, "pads": pads,
            "net": gross - charges - pads}  # fmt: skip


def run(signal: str, horizon: str, sessions: Sequence[Session], rates: FuturesRates, pad: float, stt=None,
        exit_by: date | None = None, signal_from: date | None = None) -> list[dict]:  # fmt: skip
    rows = []
    for i in range(1, len(sessions)):
        if signal_from is not None and sessions[i].day < signal_from:
            continue
        found = trade(signal, horizon, sessions, i, rates, pad, stt)
        if found is not None and (exit_by is None or found["exit"] <= exit_by.isoformat()):
            rows.append(found)
    return rows
