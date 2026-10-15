"""A fake Groww SDK client for the adapter's tests (story A16): answers the read-only calls the adapter uses and fails
on every order, position, margin or funds call, so any such call fails the test."""

from __future__ import annotations

from datetime import date

FORBIDDEN = (
    "place_order", "modify_order", "cancel_order", "create_smart_order", "modify_smart_order", "cancel_smart_order",
    "get_positions_for_user", "get_position_for_trading_symbol", "get_holdings_for_user",
    "get_available_margin_details", "get_order_margin_details", "get_order_list", "get_order_status",
    "get_order_detail", "get_trade_list_for_order", "generate_socket_token",
)  # fmt: skip
STRIKES = range(22000, 28050, 50)


class ForbiddenCall(AssertionError):
    pass


class FakeGrowwApi:
    EXCHANGE_NSE, SEGMENT_CASH, SEGMENT_FNO = "NSE", "CASH", "FNO"

    def __init__(self, index_level: float = 25000.0, fail: tuple[str, ...] = (), error: Exception | None = None):
        self.index_level, self.fail, self.error = index_level, fail, error or RuntimeError("Bad Request")
        self.calls: list[str] = []

    def __getattr__(self, name):
        if name in FORBIDDEN:
            raise ForbiddenCall(f"the recorder called {name}")
        raise AttributeError(name)

    def get_quote(self, trading_symbol, exchange, segment, timeout=None):
        self.calls.append(f"quote {trading_symbol}")
        if trading_symbol in self.fail:
            raise self.error
        if segment == self.SEGMENT_CASH:
            return {"payload": {"last_price": self.index_level, "last_trade_time": 1792036800000}}
        return {"payload": {"bid_price": 10.5, "offer_price": 11.0, "bid_quantity": 75, "offer_quantity": 150,
                            "last_trade_time": 1792036790}}  # fmt: skip

    def get_option_chain(self, exchange, underlying, expiry_date, timeout=None):
        self.calls.append(f"chain {expiry_date}")
        if f"chain {expiry_date}" in self.fail:
            raise self.error
        tag = date.fromisoformat(expiry_date).strftime("%y%m%d")  # each expiry its own symbols
        legs = {str(k): {kind: {"ltp": 1.0, "trading_symbol": f"NIFTY{tag}{k}{kind}"} for kind in ("CE", "PE")}
                for k in STRIKES}  # fmt: skip
        return {"payload": {"underlying_ltp": self.index_level, "strikes": legs}}


class FakeGrowwProvider:
    """Stands in for `GrowwProvider`: the adapter uses only `.api` and `fallback_lot_size`."""

    def __init__(self, api: FakeGrowwApi | None = None, sign_in_error: Exception | None = None):
        self._api, self.sign_in_error = api or FakeGrowwApi(), sign_in_error

    @property
    def api(self):
        if self.sign_in_error:
            raise self.sign_in_error
        return self._api

    def fallback_lot_size(self, underlying: str) -> int:
        return 75
