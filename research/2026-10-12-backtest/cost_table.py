"""Model cost and payoff table for NIFTY debit spreads (answers ChatGPT review 2, section 3).

Run from the repository root:  python research/2026-10-12-backtest/cost_table.py
Black-Scholes model marks (no bid-ask, no slippage, no tax), current Groww charges from the frozen config.
Scenario arithmetic only: it shows costs and sensitivity, not expectancy or profitability.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fno.analytics import bs_price  # noqa: E402
from fno.config import load_config  # noqa: E402
from fno.costs import order_charges  # noqa: E402

SPOT = 22370.0  # NIFTY last 5-minute close in the frozen data (12 Oct 2026)
LONG_STRIKE = 22350.0  # nearest listed strike
LOT = 65
RATE = 0.065  # as fno/backtest/option_model.py; no dividend yield
DAYS_AT_ENTRY = 37  # calendar days to expiry
DAYS_HELD = 14  # calendar days, an illustration of 10 sessions; real sessions come from the exchange calendar
VOLS = (0.12, 0.15)
WIDTHS = (50, 100, 200)
MOVES = (-0.02, -0.01, 0.0, 0.01, 0.02)  # in the spread's favour: up for calls, down for puts
PROFILES = {"Rs 2 lakh at 1%": 2000, "Rs 2 lakh at 2%": 4000, "Rs 5 lakh at 1%": 5000}


def legs(kind: str, width: int) -> tuple[float, float]:
    short = LONG_STRIKE + width if kind == "CE" else LONG_STRIKE - width
    return LONG_STRIKE, short


def spread_value(spot: float, days: float, vol: float, kind: str, width: int) -> tuple[float, float]:
    long_strike, short_strike = legs(kind, width)
    years = days / 365
    return bs_price(spot, long_strike, years, RATE, vol, kind), bs_price(spot, short_strike, years, RATE, vol, kind)


def main() -> None:
    charges = load_config(Path(__file__).parent / "inputs" / "config.yaml")["charges"]
    fee = lambda price, side: order_charges(price, LOT, side, charges)  # noqa: E731
    print(f"NIFTY {SPOT:,.0f}, lot {LOT}, {DAYS_AT_ENTRY} days to expiry, exit after {DAYS_HELD} calendar days\n")
    print(
        "| Spread | Vol | Debit (max contract loss) | Entry fees | Exit-fee reserve | Admission total | Fits |"
        " Net at -2% / -1% / 0 / +1% / +2% in its favour |"
    )
    print("|---|---|---|---|---|---|---|---|")
    for kind in ("CE", "PE"):
        for width in WIDTHS:
            for vol in VOLS:
                long_in, short_in = spread_value(SPOT, DAYS_AT_ENTRY, vol, kind, width)
                debit = (long_in - short_in) * LOT
                entry_fees = fee(long_in, "buy") + fee(short_in, "sell")
                exit_reserve = fee(long_in, "sell") + fee(short_in, "buy")  # closing at entry prices
                admission = debit + entry_fees + exit_reserve
                fits = ", ".join(name for name, cap in PROFILES.items() if admission <= cap) or "none"
                nets = []
                for move in MOVES:
                    spot = SPOT * (1 + move if kind == "CE" else 1 - move)
                    long_out, short_out = spread_value(spot, DAYS_AT_ENTRY - DAYS_HELD, vol, kind, width)
                    exit_fees = fee(long_out, "sell") + fee(short_out, "buy")
                    nets.append((long_out - short_out) * LOT - debit - entry_fees - exit_fees)
                name = f"{'bull call' if kind == 'CE' else 'bear put'} {width}"
                print(
                    f"| {name} | {vol:.0%} | {debit:,.0f} | {entry_fees:,.0f} | {exit_reserve:,.0f} |"
                    f" {admission:,.0f} | {fits} | {' / '.join(f'{n:+,.0f}' for n in nets)} |"
                )


if __name__ == "__main__":
    main()
