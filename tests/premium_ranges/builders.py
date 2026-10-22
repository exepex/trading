"""Synthetic G13 3 pm records in the stored format."""

from __future__ import annotations

from datetime import date


def contract(strike: float, kind: str, price: float, iv_points: float | None = 14.0, delta: float | None = 0.5,
             two_sided: bool = True) -> dict:  # fmt: skip
    bid, ask = (price - 0.5, price + 0.5) if two_sided else (None, price + 0.5)
    return {"strike": strike, "kind": kind, "price": price, "iv_points": iv_points, "delta": delta, "bid": bid,
            "ask": ask}  # fmt: skip


def expiry(when: date, days: int, contracts: list[dict], forward=23000.0, atm=14.0, ok=True) -> dict:
    return {"expiry": when.isoformat(), "days": days, "forward": forward, "atm_iv_points": atm,
            "distribution": {"status": "ok" if ok else "missing"}, "contracts": contracts}  # fmt: skip


def g13_record(day: date, expiries: list[dict], underlying="NIFTY", source="nse") -> dict:
    return {"underlying": underlying, "day": day.isoformat(), "source": source, "rate": 0.065,
            "method_sha256": "g" * 64, "inputs_sha256": "i" * 64, "valuation": {"expiries": expiries}}  # fmt: skip
