"""Groww's part of a slot (story MS-P0b section 2): six near-month futures quotes, four stock chains and one quote per
near-money leg (the chain has no bid or ask, P0 probe 1). Reads only through A16's `ReadOnlyGroww`; every call goes
through the slot's `PacedCaller`. The client is touched inside each request only, so a failed sign-in is one answer
the caller judges (a stop), never a second sign-in."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime

from ...providers.groww import _payload, parse_groww_chain, parse_groww_quote_book
from .answers import RawAnswer
from .caller import PacedCaller
from .constants import CHAINS, FUTURES, GROWW_FUTURE_SYMBOL, OPTION_TYPES, RowKind
from .rows import captured, missing
from .slot_capture import LotLookup, SlotCapture, near_money, near_monthly


def future_symbol(underlying: str, expiry: date) -> str:
    return GROWW_FUTURE_SYMBOL.format(underlying=underlying, expiry=expiry, month=f"{expiry:%b}".upper())


class GrowwAnswers:
    """Turns an SDK call into a `RawAnswer`: an error becomes its code, timeout and rate-limit flags and class name."""

    def __init__(self, rate_limited: Callable[[Exception], bool]):
        self.rate_limited = rate_limited

    def ask(self, request: Callable[[], object], shape: Callable[[object], bool]) -> RawAnswer:
        try:
            payload = _payload(request())
        except Exception as error:  # any SDK or sign-in error is judged, never raised past the caller
            code = str(getattr(error, "code", "") or "")
            return RawAnswer(status=int(code) if code.isdigit() else None, rate_limited=self.rate_limited(error),
                             timed_out="Timeout" in type(error).__name__, error_name=type(error).__name__)  # fmt: skip
        return RawAnswer(payload=payload, shape_ok=shape(payload))


def _is_dict(payload: object) -> bool:
    return isinstance(payload, dict)


def _has_strikes(payload: object) -> bool:
    return isinstance(payload, dict) and bool(payload.get("strikes"))


def _has_expiries(payload: object) -> bool:
    return isinstance(payload, dict) and isinstance(payload.get("expiries"), list)


class GrowwReader:
    def __init__(self, client, answers: GrowwAnswers, lot: LotLookup, now: Callable[[], datetime]):
        self.client, self.answers, self.lot, self.now = client, answers, lot, now
        self.expiries: dict[str, date | None] = {}

    def read_expiries(self, caller: PacedCaller, session: date) -> None:
        """Once a day: each underlying's near-month expiry from this year's listing."""
        for underlying in FUTURES:
            answer = caller.call("expiries", lambda u=underlying: self.answers.ask(
                lambda: self.client.get_expiries(exchange=self.client.EXCHANGE_NSE, underlying_symbol=u,
                                                 year=session.year), _has_expiries))  # fmt: skip
            listed = [date.fromisoformat(d) for d in answer.payload["expiries"]] if answer else []
            self.expiries[underlying] = near_monthly(listed, session)

    def read_slot(self, caller: PacedCaller, capture: SlotCapture) -> None:
        last = {underlying: self._future(caller, capture, underlying) for underlying in FUTURES}
        for underlying in CHAINS:
            self._chain(caller, capture, underlying, last.get(underlying))

    def _quote(self, symbol: str):
        return self.answers.ask(lambda: self.client.get_quote(trading_symbol=symbol, exchange=self.client.EXCHANGE_NSE,
                                                              segment=self.client.SEGMENT_FNO), _is_dict)  # fmt: skip

    def _future(self, caller: PacedCaller, capture: SlotCapture, underlying: str) -> float | None:
        expiry = self.expiries.get(underlying)
        if expiry is None:
            capture.rows.append(missing(RowKind.FUTURE, underlying, "", None, self.now()))
            return None
        symbol = future_symbol(underlying, expiry)
        return self._quoted(caller, capture, RowKind.FUTURE, underlying, symbol, expiry)

    def _quoted(self, caller, capture, kind, underlying: str, symbol: str, expiry: date) -> float | None:
        answer = caller.call(kind.value, lambda: self._quote(symbol))
        seen = self.now()
        if answer is None:
            capture.rows.append(missing(kind, underlying, symbol, expiry, seen))
            return None
        book = parse_groww_quote_book(symbol, answer.payload)
        digest = capture.keep(f"quote {symbol}", seen, answer)
        capture.rows.append(captured(kind, underlying, symbol, expiry, self.lot(underlying, expiry), book.bid,
                                     book.ask, book.last_trade_time, seen, digest))  # fmt: skip
        return book.last

    def _chain(self, caller, capture: SlotCapture, underlying: str, future_last: float | None) -> None:
        expiry = self.expiries.get(underlying)
        if expiry is None:
            return
        answer = caller.call(
            "chain",
            lambda: self.answers.ask(
                lambda: self.client.get_option_chain(
                    exchange=self.client.EXCHANGE_NSE, underlying=underlying, expiry_date=expiry.isoformat()
                ),
                _has_strikes,
            ),
        )
        seen = self.now()
        if answer is None:
            capture.rows.append(missing(RowKind.OPTION, underlying, "chain", expiry, seen))
            return
        capture.keep(f"chain {underlying} {expiry}", seen, answer)
        chain = parse_groww_chain(answer.payload, underlying, expiry, 0, at=seen)
        for strike in near_money([s for s, _ in chain.quotes], future_last or chain.spot):
            for kind in OPTION_TYPES:
                leg = chain.get(strike, kind)
                if leg is not None and leg.symbol:
                    self._quoted(caller, capture, RowKind.OPTION, underlying, leg.symbol, expiry)
                else:
                    capture.rows.append(missing(RowKind.OPTION, underlying, f"{strike:g}{kind}", expiry, seen))
