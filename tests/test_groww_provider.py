from datetime import datetime

from fno.config import load_config
from fno.constants import ENV_GROWW_ACCESS_TOKEN, ENV_GROWW_API_KEY
from fno.models import IST
from fno.providers import get_provider
from fno.providers.groww import token_day


def test_token_window_turns_over_at_six_ist():
    before = datetime(2026, 10, 13, 5, 59, tzinfo=IST)
    after = datetime(2026, 10, 13, 6, 0, tzinfo=IST)
    assert token_day(before).isoformat() == "2026-10-12"
    assert token_day(after).isoformat() == "2026-10-13"


def test_auto_uses_free_nse_without_groww_credentials(monkeypatch):
    monkeypatch.delenv(ENV_GROWW_ACCESS_TOKEN, raising=False)
    monkeypatch.delenv(ENV_GROWW_API_KEY, raising=False)
    assert get_provider("auto", load_config()).name == "nse"


def test_a_key_alone_is_not_a_usable_groww_login_and_auto_falls_back(monkeypatch):
    from fno.constants import ENV_GROWW_API_SECRET, ENV_GROWW_TOTP_SECRET
    from fno.providers.groww import has_groww_credentials

    monkeypatch.delenv(ENV_GROWW_ACCESS_TOKEN, raising=False)
    monkeypatch.delenv(ENV_GROWW_TOTP_SECRET, raising=False)
    monkeypatch.delenv(ENV_GROWW_API_SECRET, raising=False)
    monkeypatch.setenv(ENV_GROWW_API_KEY, "k")
    assert not has_groww_credentials()
    assert get_provider("auto", load_config()).name == "nse"
    monkeypatch.setenv(ENV_GROWW_TOTP_SECRET, "JBSWY3DPEHPK3PXP")
    assert has_groww_credentials()
    assert get_provider("auto", load_config()).name in ("groww", "nse")  # nse when the SDK is not installed


def test_groww_signs_in_again_after_the_six_am_expiry(monkeypatch):
    import fno.providers.groww as groww

    signed_in = []

    class FakeApi:
        def __init__(self, token):
            signed_in.append(token)

    provider = groww.GrowwProvider.__new__(groww.GrowwProvider)
    provider.GrowwAPI, provider._api, provider._api_day = FakeApi, None, None
    provider._token = lambda: f"token{len(signed_in)}"
    clock = iter(
        [
            datetime(2026, 10, 13, 9, 0, tzinfo=IST),
            datetime(2026, 10, 13, 15, 0, tzinfo=IST),
            datetime(2026, 10, 14, 5, 59, tzinfo=IST),
            datetime(2026, 10, 14, 6, 1, tzinfo=IST),
        ]
    )
    monkeypatch.setattr(groww, "now_ist", lambda: next(clock))
    for _ in range(4):
        assert provider.api is not None
    assert signed_in == ["token0", "token1"]  # once on the 13th's token, again only after 06:00 on the 14th


def test_expiries_skip_the_future_year_that_groww_refuses(monkeypatch):
    from datetime import date as d

    import pytest

    import fno.providers.groww as groww

    class FakeApi:
        EXCHANGE_NSE = "NSE"

        def get_expiries(self, exchange, underlying_symbol, year):
            if year > 2026:
                raise RuntimeError("Year cannot be in the future")
            return {"expiries": ["2026-10-27", "2026-11-24", "2026-01-27"]}

    provider = groww.GrowwProvider.__new__(groww.GrowwProvider)
    monkeypatch.setattr(groww, "now_ist", lambda: datetime(2026, 10, 12, 15, 0, tzinfo=IST))
    provider._api, provider._api_day = FakeApi(), groww.token_day(groww.now_ist())
    assert provider.expiries("NIFTY") == [d(2026, 10, 27), d(2026, 11, 24)]

    class BrokenApi(FakeApi):
        def get_expiries(self, exchange, underlying_symbol, year):
            raise RuntimeError("service down")

    provider._api = BrokenApi()
    with pytest.raises(RuntimeError):
        provider.expiries("NIFTY")  # a failure for the current year is never hidden


def test_groww_quote_book_uses_best_fields_else_depth_and_keeps_trade_time():
    from fno.providers.groww import parse_groww_quote_book

    live = {"bid_price": 99.5, "offer_price": 100.5, "bid_quantity": 650, "offer_quantity": 325, "last_price": 100.0,
            "last_trade_time": 1791799793, "depth": {"buy": [{"price": 1, "quantity": 1}]}}  # fmt: skip
    book = parse_groww_quote_book("NIFTY26OCT22350CE", live)
    assert (book.bid, book.ask, book.bid_qty, book.ask_qty, book.book_source) == (99.5, 100.5, 650, 325, "fields")
    assert book.last_trade_time.utcoffset().total_seconds() == 19800 and len(book.raw_sha256) == 64
    closed = {"last_price": 280.3, "depth": {"buy": [{"price": 279.75, "quantity": 455}], "sell": [{"price": 281.0,
              "quantity": 65}]}}  # fmt: skip
    book = parse_groww_quote_book("x", closed)
    assert (book.bid, book.ask, book.book_source, book.last_trade_time) == (279.75, 281.0, "depth", None)
    empty = parse_groww_quote_book("x", {})
    assert (empty.bid, empty.ask, empty.book_source) == (None, None, "")
