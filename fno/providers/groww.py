"""Groww Trade API provider (read-only: market data only, never places orders).

Credentials come from environment variables, never from files in this repo:
  GROWW_ACCESS_TOKEN                      a ready access token, or
  GROWW_API_KEY + GROWW_API_SECRET        approval-flow key/secret, or
  GROWW_API_KEY + GROWW_TOTP_SECRET       TOTP-flow key plus the TOTP seed (needs `pyotp`)
"""

from __future__ import annotations

import os
from datetime import date, datetime

from ..models import MarketContext, OptionChain, OptionQuote, now_ist
from .base import Provider
from .public import PublicData


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


class GrowwProvider(Provider):
    name = "groww"

    def __init__(self, config: dict, public: PublicData | None = None):
        super().__init__(config)
        try:
            from growwapi import GrowwAPI
        except ImportError as exc:  # pragma: no cover - depends on optional install
            raise RuntimeError("Install the Groww SDK first: pip install growwapi") from exc
        self.GrowwAPI = GrowwAPI
        self.api = GrowwAPI(self._token())
        # VIX and daily history still come from public sources.
        self.public = public or PublicData()

    def _token(self) -> str:
        token = os.environ.get("GROWW_ACCESS_TOKEN")
        if token:
            return token
        key = os.environ.get("GROWW_API_KEY")
        if not key:
            raise RuntimeError(
                "Groww credentials missing: set GROWW_ACCESS_TOKEN, or GROWW_API_KEY with "
                "GROWW_API_SECRET or GROWW_TOTP_SECRET as environment secrets."
            )
        secret = os.environ.get("GROWW_API_SECRET")
        if secret:
            return self.GrowwAPI.get_access_token(api_key=key, secret=secret)
        totp_seed = os.environ.get("GROWW_TOTP_SECRET")
        if totp_seed:
            import pyotp

            return self.GrowwAPI.get_access_token(api_key=key, totp=pyotp.TOTP(totp_seed).now())
        raise RuntimeError("Set GROWW_API_SECRET or GROWW_TOTP_SECRET alongside GROWW_API_KEY.")

    def expiries(self, underlying: str) -> list[date]:
        today = now_ist().date()
        found: set[date] = set()
        for year in (today.year, today.year + 1):
            resp = _payload(
                self.api.get_expiries(exchange=self.api.EXCHANGE_NSE, underlying_symbol=underlying.upper(), year=year)
            )
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
