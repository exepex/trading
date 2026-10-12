"""Three ledgers so that "profitable" always means money actually kept (story C1, design section 8).

1. Trade ledger: each trade's gross P&L at quoted prices, the cost of the assumed worse fills (pads), every charge by
   component (from `fno.costs`, the single charges model) and the net.
2. Account ledger: trade net by month minus the desk's own operating costs (AI, data), entered as actual amounts.
3. Tax: one **assumed scenario**, not a verified tax liability: Indian financial year (April-March); base = the year's
   trade net minus operating costs in categories declared deductible; tax = rate x max(0, base); losses offset within
   the year; no carry-forward modelled. Tax never enters a research pass/fail.
"""

from __future__ import annotations

import csv
import io
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from ..costs import CHARGE_NAMES, order_charges_breakdown

DEFAULT_TAX_RATE_PCT = 31.2  # owner decision: 30% slab + 4% cess, on the year's net F&O profit
TAX_LABEL = "assumed scenario (30% slab + 4% cess on yearly net F&O profit), not a verified tax liability"
NO_CARRY_FORWARD = "loss shown; carry-forward to later years is not modelled"
COST_COLUMNS = ("month", "item", "category", "amount_rs", "source")


@dataclass(frozen=True)
class Order:
    side: str  # "buy" or "sell"
    quoted_price: float  # the price the market showed
    units: int  # lots x lot size
    pad: float = 0.0  # rupees per unit worse than quoted (assumed slippage)

    @property
    def fill_price(self) -> float:
        return self.quoted_price + self.pad if self.side == "buy" else max(self.quoted_price - self.pad, 0.0)


@dataclass(frozen=True)
class Trade:
    trade_id: str
    closed_on: date
    orders: tuple[Order, ...]


@dataclass
class TradeLine:
    trade_id: str
    closed_on: date
    gross: float  # at quoted prices
    pads: float  # cost of the assumed worse fills
    charges: dict[str, float] = field(default_factory=dict)  # by component, on the fill prices

    @property
    def net(self) -> float:
        return self.gross - self.pads - sum(self.charges.values())


def trade_line(trade: Trade, charges_table: dict) -> TradeLine:
    sign = {"buy": -1.0, "sell": 1.0}
    gross = sum(sign[o.side] * o.quoted_price * o.units for o in trade.orders)
    fills = sum(sign[o.side] * o.fill_price * o.units for o in trade.orders)
    charges = dict.fromkeys(CHARGE_NAMES, 0.0)
    for order in trade.orders:
        for name, value in order_charges_breakdown(order.fill_price, order.units, order.side, charges_table).items():
            charges[name] += value
    return TradeLine(trade.trade_id, trade.closed_on, gross, gross - fills, charges)


def financial_year(day: date) -> str:
    """Indian financial year label, e.g. 31 Mar 2025 -> "2024-25", 1 Apr 2025 -> "2025-26"."""
    start = day.year if day.month >= 4 else day.year - 1
    return f"{start}-{(start + 1) % 100:02d}"


def read_operating_costs(text: str) -> list[dict]:
    rows = list(csv.DictReader(io.StringIO(text)))
    for row in rows:
        if tuple(row) != COST_COLUMNS:
            raise ValueError(f"operating costs columns must be {COST_COLUMNS}")
        float(row["amount_rs"])
        date.fromisoformat(row["month"] + "-01")
    return rows


def read_deductible(text: str) -> set[str]:
    return {r["category"] for r in csv.DictReader(io.StringIO(text)) if r["deductible"].strip().lower() == "yes"}


@dataclass
class Ledgers:
    trades: list[TradeLine]
    operating_costs: list[dict]
    deductible: set[str]
    tax_rate_pct: float = DEFAULT_TAX_RATE_PCT

    def by_month(self) -> dict[str, dict[str, float]]:
        months: dict[str, dict[str, float]] = defaultdict(lambda: {"trade_net": 0.0, "operating_costs": 0.0})
        for line in self.trades:
            months[line.closed_on.strftime("%Y-%m")]["trade_net"] += line.net
        for cost in self.operating_costs:
            months[cost["month"]]["operating_costs"] += float(cost["amount_rs"])
        for values in months.values():
            values["account_result"] = values["trade_net"] - values["operating_costs"]
        return dict(sorted(months.items()))

    def tax_by_year(self) -> dict[str, dict]:
        years: dict[str, dict] = defaultdict(
            lambda: {"trade_net": 0.0, "operating_costs": 0.0, "deductible_costs": 0.0}
        )
        for line in self.trades:
            years[financial_year(line.closed_on)]["trade_net"] += line.net
        for cost in self.operating_costs:
            year = years[financial_year(date.fromisoformat(cost["month"] + "-01"))]
            year["operating_costs"] += float(cost["amount_rs"])
            if cost["category"] in self.deductible:
                year["deductible_costs"] += float(cost["amount_rs"])
        for values in years.values():
            values["account_result"] = values["trade_net"] - values["operating_costs"]
            values["tax_base"] = values["trade_net"] - values["deductible_costs"]
            values["tax"] = self.tax_rate_pct / 100 * max(0.0, values["tax_base"])
            values["after_tax"] = values["account_result"] - values["tax"]
            values["label"] = TAX_LABEL
            if values["tax_base"] < 0:
                values["note"] = NO_CARRY_FORWARD
        return dict(sorted(years.items()))

    def reconciles(self) -> bool:
        """Account result = trade net - operating costs, and tax base = trade net - deductible costs, every year."""
        trade_total = sum(t.net for t in self.trades)
        cost_total = sum(float(c["amount_rs"]) for c in self.operating_costs)
        months = self.by_month()
        years = self.tax_by_year()
        month_ok = abs(sum(m["account_result"] for m in months.values()) - (trade_total - cost_total)) < 0.01
        year_ok = all(
            abs(y["account_result"] - (y["trade_net"] - y["operating_costs"])) < 0.01
            and abs(y["tax_base"] - (y["trade_net"] - y["deductible_costs"])) < 0.01
            for y in years.values()
        )
        return month_ok and year_ok
