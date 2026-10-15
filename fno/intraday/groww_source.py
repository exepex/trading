"""Groww as the 15-minute snapshot source (story A16). Read-only: only `get_quote` and `get_option_chain` here, plus
the existing provider's sign-in and expiry list; no order, position, margin or funds call exists in this package.
Credentials stay in the environment (`GrowwProvider`); a failure is kept by its exception class name only.

Order inside a snapshot: the index quote first (the realised variance's input, sent right at the mark), then the near
future, the two chains, and one quote per contract within 6% of the index level, at most 4 at a time and 5 a second
(step 0's measured limit)."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime

from ..models import IST, now_ist
from ..providers.groww import GrowwProvider, _payload, parse_groww_chain, parse_groww_quote_book
from .document import CallRecord, SnapshotDocument
from .expiry_plan import UNDERLYING, Expiries, ExpiryPlan
from .pacing import RatePacer
from .source import IntradayQuoteSource

SPOT_BAND = 0.06  # strikes within 6% of the index level (design 2.1)
INDEX_SYMBOL = "NIFTY"
FUTURE_SYMBOL = "NIFTY{expiry:%y}{month}FUT"  # e.g. NIFTY26OCTFUT (step 0: the form get_quote accepts)
WORKERS, PER_SECOND = 4, 5
EXPIRY_PLAN = "expiry_plan"
MILLISECONDS_FROM = 10**11  # an epoch time above this is in milliseconds


class GrowwIntradaySource(IntradayQuoteSource):
    name = "groww"

    def __init__(self, provider: GrowwProvider, plan: ExpiryPlan, clock: Callable[[], datetime] = now_ist,
                 pacer: RatePacer | None = None):  # fmt: skip
        self.provider, self.plan, self.clock = provider, plan, clock
        self.pacer = pacer or RatePacer(PER_SECOND)
        self._expiries: dict[date, Expiries] = {}
        self._prepare_failures: list[str] = []

    def prepare(self, session: date) -> None:
        self._prepare_failures = []
        for step, action in (("sign_in", lambda: self.provider.api), (EXPIRY_PLAN, lambda: self._plan(session))):
            try:
                action()
            except Exception as exc:  # kept by name; the snapshot still tries every call
                self._prepare_failures.append(f"{step}: {type(exc).__name__}")

    def take(self, session: date, mark: datetime) -> SnapshotDocument:
        index = self._call("index", lambda api: api.get_quote(
            trading_symbol=INDEX_SYMBOL, exchange=api.EXCHANGE_NSE, segment=api.SEGMENT_CASH))  # fmt: skip
        level, source_time = _index_reading(index.payload)
        doc = SnapshotDocument(self.name, UNDERLYING, session, mark, index, level, source_time,
                               failures=list(self._prepare_failures))  # fmt: skip
        try:
            expiries = self._plan(session)
        except Exception as exc:
            doc.failures.append(f"{EXPIRY_PLAN}: {type(exc).__name__}")
            return self._finish(doc)
        doc.expiries = expiries.to_json()
        doc.future = self._future(expiries.monthly)
        chains = [self._chain(expiry) for expiry in expiries.chains]
        doc.chains = [record for record, _ in chains]
        contracts = [c for _, chain in chains if chain for c in self._contracts(chain, level or chain.spot)]
        doc.expected_contracts = len(contracts)
        with ThreadPoolExecutor(WORKERS) as pool:
            doc.quotes = list(pool.map(self._quote, contracts))
        doc.two_sided_contracts = sum(1 for q in doc.quotes if _two_sided(q))
        doc.failures += [r.name for r in [index, doc.future, *doc.chains, *doc.quotes] if r.failure]
        return self._finish(doc)

    def _finish(self, doc: SnapshotDocument) -> SnapshotDocument:
        doc.finished_at = self.clock()
        return doc

    def _plan(self, session: date) -> Expiries:
        if session not in self._expiries:
            self._expiries = {session: self.plan.plan(session)}
        return self._expiries[session]

    def _call(self, name: str, request, meta: dict | None = None) -> CallRecord:
        sent = self.clock()
        try:
            payload = _payload(request(self.provider.api))
        except Exception as exc:  # the class name only: an exception's text could carry a credential
            return CallRecord(name, sent, None, None, type(exc).__name__, meta or {})
        return CallRecord(name, sent, self.clock(), payload, "", meta or {})

    def _future(self, monthly: date) -> CallRecord:
        symbol = FUTURE_SYMBOL.format(expiry=monthly, month=f"{monthly:%b}".upper())
        return self._call(f"future {symbol}", lambda api: api.get_quote(
            trading_symbol=symbol, exchange=api.EXCHANGE_NSE, segment=api.SEGMENT_FNO), {"symbol": symbol})  # fmt: skip

    def _chain(self, expiry: date):
        record = self._call(f"chain {expiry}", lambda api: api.get_option_chain(
            exchange=api.EXCHANGE_NSE, underlying=UNDERLYING, expiry_date=expiry.isoformat()),
            {"expiry": expiry.isoformat()})  # fmt: skip
        if record.failure:
            return record, None
        lot = self.provider.fallback_lot_size(UNDERLYING)
        return record, parse_groww_chain(record.payload, UNDERLYING, expiry, lot, record.response_received_at)

    @staticmethod
    def _contracts(chain, level: float) -> list[dict]:
        low, high = level * (1 - SPOT_BAND), level * (1 + SPOT_BAND)
        picked = sorted((strike, kind, q.symbol) for (strike, kind), q in chain.quotes.items() if low <= strike <= high)
        return [{"expiry": chain.expiry.isoformat(), "strike": s, "type": k, "symbol": sym} for s, k, sym in picked]

    def _quote(self, contract: dict) -> CallRecord:
        if not contract["symbol"]:
            return CallRecord(f"quote {contract['expiry']} {contract['strike']:g} {contract['type']}", self.clock(),
                              None, None, "NoTradingSymbol", contract)  # fmt: skip
        symbol = contract["symbol"]
        self.pacer.wait()
        return self._call(f"quote {symbol}", lambda api: api.get_quote(
            trading_symbol=symbol, exchange=api.EXCHANGE_NSE, segment=api.SEGMENT_FNO), contract)  # fmt: skip


def _index_reading(payload) -> tuple[float | None, datetime | None]:
    """The index level and Groww's own time for it (its `last_trade_time`, epoch seconds or milliseconds)."""
    if not isinstance(payload, dict):
        return None, None
    level = payload.get("last_price")
    return (float(level) if level else None), epoch_time(payload.get("last_trade_time"))


def epoch_time(value) -> datetime | None:
    if not value:
        return None
    number = int(value)
    return datetime.fromtimestamp(number / 1000 if number > MILLISECONDS_FROM else number, IST)


def _two_sided(record: CallRecord) -> bool:
    if record.failure or not isinstance(record.payload, dict):
        return False
    book = parse_groww_quote_book(record.meta.get("symbol", ""), record.payload)
    return bool(book.bid and book.ask)
