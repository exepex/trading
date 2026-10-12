"""Groww Trade API provider (read-only: market data only, never places orders).

Credentials come from environment variables, never from files in this repo:
  GROWW_ACCESS_TOKEN                      a ready access token, or
  GROWW_API_KEY + GROWW_API_SECRET        approval-flow key/secret, or
  GROWW_API_KEY + GROWW_TOTP_SECRET       TOTP-flow key plus the TOTP seed (needs `pyotp`)

Groww access tokens expire every morning at 06:00 IST. With a key plus TOTP seed (recommended: no daily approval)
or key plus secret, the provider fetches a new token by itself after that time, so the desk runs unattended.
Market-data calls need no fixed IP address; SEBI's static-IP rule applies to placing orders, which this never does.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime, time, timedelta

from ..constants import ENV_GROWW_ACCESS_TOKEN, ENV_GROWW_API_KEY, ENV_GROWW_API_SECRET, ENV_GROWW_TOTP_SECRET
from ..models import IST, MarketContext, OptionChain, OptionQuote, QuoteBook, now_ist
from .base import Provider
from .public import PublicData

TOKEN_EXPIRY_TIME_IST = time(6, 0)
CREDENTIALS_MISSING = (
    f"Groww credentials missing: set {ENV_GROWW_API_KEY} with {ENV_GROWW_TOTP_SECRET} (or {ENV_GROWW_API_SECRET}), "
    f"or a ready {ENV_GROWW_ACCESS_TOKEN}, in ~/.trading.env."
)


def has_groww_credentials() -> bool:
    """A usable set: a ready token, or a key with its TOTP seed or secret. A key alone cannot sign in."""
    key = os.environ.get(ENV_GROWW_API_KEY)
    paired = key and (os.environ.get(ENV_GROWW_TOTP_SECRET) or os.environ.get(ENV_GROWW_API_SECRET))
    return bool(os.environ.get(ENV_GROWW_ACCESS_TOKEN) or paired)


def token_day(moment: datetime) -> date:
    """Tokens live from 06:00 IST to 06:00 the next day; this names the window a moment falls in."""
    return (moment - timedelta(hours=TOKEN_EXPIRY_TIME_IST.hour, minutes=TOKEN_EXPIRY_TIME_IST.minute)).date()


def _payload(resp: dict) -> dict:
    return resp.get("payload", resp) if isinstance(resp, dict) else resp


def parse_groww_chain(
    resp: dict, underlying: str, expiry: date, lot_size: int, at: datetime | None = None
) -> OptionChain:
    data = _payload(resp)
    quotes: dict[tuple[float, str], OptionQuote] = {}
    for strike_text, legs in (data.get("strikes") or {}).items():
        strike = float(strike_text)
        for kind in ("CE", "PE"):
            leg = (legs or {}).get(kind)
            if not leg:
                continue
            greeks = leg.get("greeks") or {}
            quotes[(strike, kind)] = OptionQuote(
                strike=strike,
                kind=kind,
                ltp=float(leg.get("ltp") or 0),
                oi=float(leg.get("open_interest") or 0),
                volume=float(leg.get("volume") or 0),
                iv=float(greeks.get("iv") or 0) or None,
                symbol=leg.get("trading_symbol"),
            )
    return OptionChain(
        underlying=underlying.upper(),
        spot=float(data.get("underlying_ltp") or 0),
        expiry=expiry,
        timestamp=at or now_ist(),
        lot_size=lot_size,
        quotes=quotes,
        source="groww",
    )


def parse_groww_quote_book(symbol: str, payload: dict) -> QuoteBook:
    """Groww's quote as a QuoteBook: best bid/offer fields when present, else the top of the market depth (marked).
    Groww gives the last trade time (Unix seconds) but no timestamp for the quote itself."""
    bid, ask = payload.get("bid_price"), payload.get("offer_price")
    bid_qty, ask_qty, source = payload.get("bid_quantity"), payload.get("offer_quantity"), "fields"
    if not bid and not ask:
        depth = payload.get("depth") or {}
        top_buy, top_sell = (depth.get("buy") or [{}])[0], (depth.get("sell") or [{}])[0]
        bid, bid_qty, ask, ask_qty = (
            top_buy.get("price"),
            top_buy.get("quantity"),
            top_sell.get("price"),
            top_sell.get("quantity"),
        )
        source = "depth" if (bid or ask) else ""
    traded = payload.get("last_trade_time")
    raw = json.dumps(payload, sort_keys=True, default=str).encode()
    return QuoteBook(
        symbol=symbol,
        bid=float(bid) if bid else None,
        ask=float(ask) if ask else None,
        bid_qty=float(bid_qty) if bid_qty else None,
        ask_qty=float(ask_qty) if ask_qty else None,
        last=float(payload["last_price"]) if payload.get("last_price") else None,
        last_trade_time=datetime.fromtimestamp(int(traded), IST) if traded else None,
        book_source=source,
        raw_sha256=hashlib.sha256(raw).hexdigest(),
    )


class GrowwProvider(Provider):
    name = "groww"

    def __init__(self, config: dict, public: PublicData | None = None):
        super().__init__(config)
        try:
            from growwapi import GrowwAPI
        except ImportError as exc:  # pragma: no cover - depends on optional install
            raise RuntimeError("Install the Groww SDK first: pip install growwapi") from exc
        self.GrowwAPI = GrowwAPI
        self._api = None
        self._api_day: date | None = None
        # VIX and daily history still come from public sources.
        self.public = public or PublicData()

    @property
    def api(self):
        """The SDK client, signed in again with a fresh token once the 06:00 IST expiry has passed."""
        today = token_day(now_ist())
        if self._api is None or self._api_day != today:
            self._api = self.GrowwAPI(self._token())
            self._api_day = today
        return self._api

    def _token(self) -> str:
        key = os.environ.get(ENV_GROWW_API_KEY)
        totp_seed = os.environ.get(ENV_GROWW_TOTP_SECRET)
        secret = os.environ.get(ENV_GROWW_API_SECRET)
        if key and totp_seed:
            import pyotp

            return self.GrowwAPI.get_access_token(api_key=key, totp=pyotp.TOTP(totp_seed).now())
        if key and secret:
            return self.GrowwAPI.get_access_token(api_key=key, secret=secret)
        token = os.environ.get(ENV_GROWW_ACCESS_TOKEN)  # a manual token: works only until the next 06:00 IST
        if token:
            return token
        raise RuntimeError(CREDENTIALS_MISSING)

    def expiries(self, underlying: str) -> list[date]:
        today = now_ist().date()
        found: set[date] = set()
        for year in (today.year, today.year + 1):
            try:
                resp = _payload(
                    self.api.get_expiries(
                        exchange=self.api.EXCHANGE_NSE, underlying_symbol=underlying.upper(), year=year
                    )
                )
            except Exception:
                if year == today.year:
                    raise
                continue  # Groww refuses any future year ("Year cannot be in the future"); this year's list suffices
            for text in resp.get("expiries", []):
                d = date.fromisoformat(text)
                if d >= today:
                    found.add(d)
        return sorted(found)

    def chain(self, underlying: str, expiry: date) -> OptionChain:
        resp = self.api.get_option_chain(
            exchange=self.api.EXCHANGE_NSE, underlying=underlying.upper(), expiry_date=expiry.isoformat()
        )
        return parse_groww_chain(resp, underlying, expiry, self.fallback_lot_size(underlying))

    def quote_book(self, chain: OptionChain, strike: float, kind: str) -> QuoteBook | None:
        leg = chain.get(strike, kind)
        if leg is None or not leg.symbol:
            return None
        payload = _payload(
            self.api.get_quote(trading_symbol=leg.symbol, exchange=self.api.EXCHANGE_NSE, segment=self.api.SEGMENT_FNO)
        )
        return parse_groww_quote_book(leg.symbol, payload)

    def context(self, underlying: str) -> MarketContext:
        history = self.public.daily_history(underlying)
        closes = [c for _, c in history]
        vix, lo, hi = self.public.vix()
        spot = closes[-1] if closes else 0.0
        return MarketContext(
            underlying=underlying.upper(),
            spot=spot,
            prev_close=closes[-2] if len(closes) > 1 else None,
            closes=closes,
            dates=[d for d, _ in history],
            vix=vix,
            vix_year_low=lo,
            vix_year_high=hi,
        )
