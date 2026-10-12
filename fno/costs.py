"""Transaction-cost model for NSE options orders placed through Groww.

Every P&L in this project is net of all of these: brokerage, STT, exchange transaction charges,
SEBI turnover fee, NSE investor-protection fund (IPFT), stamp duty, and GST (CGST + SGST, or IGST) on
brokerage + exchange + SEBI + IPFT charges.
"""

from __future__ import annotations

CHARGE_NAMES = {
    "brokerage": "Brokerage",
    "stt": "STT (securities transaction tax)",
    "exchange": "Exchange transaction charges",
    "sebi": "SEBI turnover fee",
    "ipft": "NSE IPFT",
    "stamp": "Stamp duty",
    "gst": "GST (central + state)",
}


def order_charges_breakdown(premium: float, units: int, side: str, charges: dict) -> dict[str, float]:
    """Each charge for one executed options order, in rupees."""
    turnover = premium * units
    out = {
        "brokerage": charges.get("brokerage_per_order", 20.0) if turnover > 0 else 0.0,
        "exchange": turnover * charges.get("exchange_txn_pct", 0.03503) / 100,
        "sebi": turnover * charges.get("sebi_per_crore", 10.0) / 1e7,
        "ipft": turnover * charges.get("ipft_per_crore", 50.0) / 1e7,
        "stt": turnover * charges.get("stt_sell_pct", 0.1) / 100 if side == "sell" else 0.0,
        "stamp": turnover * charges.get("stamp_duty_buy_pct", 0.003) / 100 if side == "buy" else 0.0,
    }
    out["gst"] = (out["brokerage"] + out["exchange"] + out["sebi"] + out["ipft"]) * charges.get("gst_pct", 18.0) / 100
    return out


def order_charges(premium: float, units: int, side: str, charges: dict) -> float:
    """All-in statutory + broker charges for one executed options order (rupees)."""
    return sum(order_charges_breakdown(premium, units, side, charges).values())
