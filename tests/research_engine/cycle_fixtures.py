"""Hand-built cycles and panels for the cycle simulator tests (story B2), with a charges model written here
independently of fno/costs.py (Groww's options charges, config.yaml values of 13 Oct 2026)."""

from __future__ import annotations

from datetime import date

from fno.constants import OPTION_CALL, OPTION_PUT, SESSION_REGULAR
from fno.research_data.panel_reader import NiftyPanel, OptionQuote, SessionClose
from fno.research_engine.cycle_costs import CycleTerms
from fno.research_engine.cycles import Cycle

EXPIRY = date(2025, 3, 27)
CYCLE = Cycle(EXPIRY, decision_day=date(2025, 2, 10), entry_day=date(2025, 2, 11), exit_day=date(2025, 3, 6))
LOT = 65
CHARGES = {
    "brokerage_per_order": 20.0, "stt_sell_pct": 0.15, "exchange_txn_pct": 0.03503, "sebi_per_crore": 10.0,
    "ipft_per_crore": 50.0, "stamp_duty_buy_pct": 0.003, "gst_pct": 18.0,
}  # fmt: skip
TERMS = CycleTerms(lot=LOT, charges=CHARGES)
CE, PE = OPTION_CALL, OPTION_PUT

Prices = dict[tuple[float, str], float]  # (strike, kind) -> close; every listed leg traded unless said otherwise


def hand_order_charges(price: float, sell: bool) -> float:
    """One order of one lot: Rs 20 brokerage, exchange 0.03503%, SEBI Rs 10 and IPFT Rs 50 per crore, STT 0.15% on
    sells, stamp 0.003% on buys, GST 18% on brokerage, exchange, SEBI and IPFT; at least one tick (Rs 0.05)."""
    turnover = max(price, 0.05) * LOT
    fees = 20 + turnover * 0.03503 / 100 + turnover * 10 / 1e7 + turnover * 50 / 1e7
    tax = turnover * 0.15 / 100 if sell else turnover * 0.003 / 100
    return fees * 1.18 + tax


def quotes(prices: Prices, settle: Prices | None = None, expiry: date = EXPIRY) -> tuple[OptionQuote, ...]:
    """Option rows: each priced leg traded (volume 100); a leg in `settle` did not trade and settles at that price."""
    rows = [OptionQuote(expiry, k, kind, close, 0.0, 100, 1000) for (k, kind), close in prices.items()]
    rows += [OptionQuote(expiry, k, kind, 0.0, price, 0, 1000) for (k, kind), price in (settle or {}).items()]
    return tuple(rows)


def cycle_panel(spot: float, entry: tuple[OptionQuote, ...], exit_: tuple[OptionQuote, ...]) -> NiftyPanel:
    sessions = (
        SessionClose(CYCLE.entry_day, SESSION_REGULAR, spot, 14.0),
        SessionClose(CYCLE.exit_day, SESSION_REGULAR, spot, 14.0),
    )
    return NiftyPanel(sessions, {CYCLE.entry_day: entry, CYCLE.exit_day: exit_}, {})


def strikes_listed(strikes: list[float], price: float = 5.0) -> Prices:
    """Both kinds at every strike, traded at `price` (filler for contracts a test does not price itself)."""
    return {(k, kind): price for k in strikes for kind in (CE, PE)}
