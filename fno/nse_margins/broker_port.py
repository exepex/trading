"""The broker side of A14c part 2: an interface (one margin per basket, one index level) and its Groww adapter, which
holds only a `ReadOnlyGroww` with this caller's own allow-list: the margin calculator, the quote and the constants they
need. The calculator creates nothing: after the four calls of 14-16 Oct the account showed 0 orders, 0 positions and
0 used or blocked margin (read-only checks, response 77 and the part 2 text)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ..constants import NIFTY_SYMBOL
from ..intraday.index_reading import quote_reading
from ..intraday.read_only import ReadOnlyGroww
from ..providers.groww import _payload

BROKER_CHECK_CALLS = frozenset({"get_order_margin_details", "get_quote", "SEGMENT_FNO", "SEGMENT_CASH", "EXCHANGE_NSE"})
CALL_TIMEOUT_SECONDS = 10  # a hung call is an error, never a stuck run
SPAN_FIELD, EXPOSURE_FIELD = "span_required", "exposure_required"


class BrokerAnswerProblem(ValueError):
    """The broker answered without a usable figure."""


class BrokerMargins(ABC):
    @abstractmethod
    def index_level(self) -> float:
        """NIFTY's last price now, from the broker, read by this caller."""

    @abstractmethod
    def basket(self, orders: Sequence[dict]) -> tuple[float, float]:
        """(SPAN, exposure) the broker's calculator gives for the basket, in rupees."""


class GrowwBrokerMargins(BrokerMargins):
    def __init__(self, client: ReadOnlyGroww):
        self.client = client

    def index_level(self) -> float:
        api = self.client
        quote = api.get_quote(trading_symbol=NIFTY_SYMBOL, exchange=api.EXCHANGE_NSE, segment=api.SEGMENT_CASH,
                              timeout=CALL_TIMEOUT_SECONDS)  # fmt: skip
        level, _ = quote_reading(_payload(quote))
        if not level or level <= 0:
            raise BrokerAnswerProblem("the NIFTY quote has no last price")
        return level

    def basket(self, orders: Sequence[dict]) -> tuple[float, float]:
        api = self.client
        answer = _payload(
            api.get_order_margin_details(segment=api.SEGMENT_FNO, orders=list(orders), timeout=CALL_TIMEOUT_SECONDS)
        )  # the SDK's default waits forever
        try:
            span, exposure = float(answer[SPAN_FIELD]), float(answer[EXPOSURE_FIELD])
        except (TypeError, KeyError, ValueError) as exc:
            raise BrokerAnswerProblem(f"the margin answer has no {SPAN_FIELD} and {EXPOSURE_FIELD}") from exc
        return span, exposure
