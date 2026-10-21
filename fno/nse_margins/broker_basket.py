"""The baskets of A14c part 2's broker check: each of today's A14 rows rebuilt from the same archived SPAN file (same
structure, width, legs, expiry and prices), proved to be that row (the file's SHA-256 and the three figures), and
written as the order list Groww's margin calculator takes. Groww ignores the limit prices sent; the file's prices go
in so the basket is the row's own."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from ..research_engine.structures import Leg
from .rows import MarginRowBuilder, span_source
from .span_file import SpanFile

SYMBOL = "NIFTY{expiry:%y}{month}{strike:g}{kind}"  # e.g. NIFTY26NOV25000CE, the form the 14-16 Oct checks used
ORDER_TYPE, PRODUCT, EXCHANGE = "LIMIT", "NRML", "NSE"
BUY, SELL = "BUY", "SELL"
FIGURE_COLUMNS = ("scan_per_lot_rs", "nov_per_lot_rs", "exposure_per_lot_rs")
NOT_REPRODUCED = "the row is not reproduced from {file}: {why}"


class BasketProblem(ValueError):
    """A row whose basket cannot be built or is not the row's own (the check records it as `error`)."""


@dataclass(frozen=True)
class Basket:
    structure: str
    width: float
    expiry: date
    legs: tuple[Leg, ...]
    prices: tuple[float, ...]  # per leg, the file's price
    scan: float  # per lot, the row's own figures
    nov: float
    exposure: float

    @property
    def key(self) -> tuple[str, float]:
        return self.structure, self.width

    @property
    def span_expected(self) -> float:
        """What Groww's `span_required` should be: the row's SPAN after the net option value, `max(0, scan - NOV)`."""
        return max(0.0, self.scan - self.nov)

    def orders(self, lot_size: int) -> list[dict]:
        month = f"{self.expiry:%b}".upper()
        return [{"trading_symbol": SYMBOL.format(expiry=self.expiry, month=month, strike=leg.strike, kind=leg.kind),
                 "transaction_type": BUY if leg.bought else SELL, "quantity": lot_size, "price": price,
                 "order_type": ORDER_TYPE, "product": PRODUCT, "exchange": EXCHANGE}
                for leg, price in zip(self.legs, self.prices, strict=True)]  # fmt: skip


class BasketBuilder:
    def __init__(self, builder: MarginRowBuilder):
        self.builder = builder
        self.structures = {structure.code: structure for structure in builder.structures}

    def basket(self, row: Mapping[str, str], span: SpanFile, data: bytes, day: date) -> Basket:
        """The row's basket from `data`, the archived file it names; refuses anything that is not that row."""
        if row["source"] != span_source(span.name, hashlib.sha256(data).hexdigest()):
            raise BasketProblem(NOT_REPRODUCED.format(file=span.name, why="its source names another file or SHA-256"))
        structure, width = self.structures.get(row["structure"]), float(row["width"])
        if structure is None:
            raise BasketProblem(f"{row['structure']} is not a structure A14 builds")
        expiry = self.builder.expiry_for(span, day)
        legs = structure.legs(frozenset(span.series.get(expiry, {})), span.underlying, width)
        if legs is None:
            raise BasketProblem(NOT_REPRODUCED.format(file=span.name, why=f"a leg is not listed for {expiry}"))
        figure = self.builder.calculator.per_lot(span, expiry, legs, day)
        rebuilt = (f"{figure.span:.2f}", f"{figure.nov:.2f}", f"{figure.exposure:.2f}")
        if rebuilt != tuple(row[column] for column in FIGURE_COLUMNS):
            raise BasketProblem(NOT_REPRODUCED.format(file=span.name, why=f"figures {', '.join(rebuilt)}"))
        prices = tuple(span.series[expiry][leg.contract].price for leg in legs)
        return Basket(structure.code, width, expiry, tuple(legs), prices, figure.span, figure.nov, figure.exposure)


def todays_rows(rows: Sequence[Mapping[str, str]], day: date) -> list[Mapping[str, str]]:
    """Today's A14 rows, in file order: every structure and width A14 wrote for `day`."""
    return [row for row in rows if row["as_of"] == day.isoformat()]
