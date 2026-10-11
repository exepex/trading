"""Transaction-cost model for NSE options orders placed through Groww."""

from __future__ import annotations


def order_charges(premium: float, units: int, side: str, charges: dict) -> float:
    """All-in statutory + broker charges for one executed options order (rupees)."""
    turnover = premium * units
    brokerage = charges.get("brokerage_per_order", 20.0) if turnover > 0 else 0.0
    txn = turnover * charges.get("exchange_txn_pct", 0.03503) / 100
    sebi = turnover * charges.get("sebi_per_crore", 10.0) / 1e7
    stt = turnover * charges.get("stt_sell_pct", 0.1) / 100 if side == "sell" else 0.0
    stamp = turnover * charges.get("stamp_duty_buy_pct", 0.003) / 100 if side == "buy" else 0.0
    gst = (brokerage + txn + sebi) * charges.get("gst_pct", 18.0) / 100
    return brokerage + txn + sebi + stt + stamp + gst


def legs_charges(legs: list[tuple[str, float]], units: int, charges: dict) -> float:
    """Charges for a set of (side, premium) orders."""
    return sum(order_charges(price, units, side, charges) for side, price in legs)
