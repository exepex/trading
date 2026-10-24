"""Synthetic G13 day records in the stored format, and fakes for the settlement readers."""

from __future__ import annotations

from datetime import date

from fno.desk.settlement import FinalSettlement, SettlementError, SettlementPrices

POINTS = [[22000.0, 0.10], [22500.0, 0.30], [23000.0, 0.55], [23500.0, 0.80], [24000.0, 0.92]]
LOWER = {"strike": 22000.0, "cdf": 0.10, "iv_points": 18.0}
UPPER = {"strike": 24000.0, "cdf": 0.92, "iv_points": 14.0}


def expiry(when: date, days: int, strikes=(22500.0, 23000.0), points=POINTS, ok=True, forward=23000.0) -> dict:
    distribution = (
        {"status": "ok", "raw_decreases": 0, "cdf": points, "lower_tail": LOWER, "upper_tail": UPPER}
        if ok
        else {"status": "missing", "reason": "too few CDF points: 3 (at least 8)"}
    )
    contracts = [{"strike": k, "kind": kind} for k in strikes for kind in ("CE", "PE")]
    return {"expiry": when.isoformat(), "days": days, "status": "ok", "reason": None, "forward": forward,
            "distribution": distribution, "contracts": contracts if ok else []}  # fmt: skip


def record(day: date, expiries: list[dict], label="backfill_eod", underlying="NIFTY", method="m" * 64) -> dict:
    return {"underlying": underlying, "day": day.isoformat(), "label": label, "method_sha256": method,
            "valuation": {"expiries": expiries}}  # fmt: skip


class FakePrices(SettlementPrices):
    def __init__(self, prices: dict[date, float | Exception]):
        self.prices, self.asked = prices, []

    def final_settlement(self, underlying: str, expiry: date) -> FinalSettlement | None:
        self.asked.append(expiry)
        found = self.prices.get(expiry)
        if isinstance(found, Exception):
            raise found
        return None if found is None else FinalSettlement(underlying, expiry, found, "path", "sha")


REFUSED = SettlementError("the expiring contracts disagree")
