from dataclasses import replace
from datetime import date

from fno import journal
from fno.config import load_config
from fno.constants import FILL_BID_ASK, FILL_LAST_PRICE, Direction
from fno.live.contract_picker import ContractPicker, ExitLevels, PickerRules
from fno.live.models import MarketView
from fno.providers.groww import parse_groww_book
from fno.providers.sample import SampleProvider

from .fakes import SESSION_DAY

CFG = load_config(overrides={"profile": "live"})
EXPIRY = date(2026, 10, 27)


def chain_without_book():
    """What Groww's option chain looks like: last prices only, no bid/ask."""
    chain = SampleProvider(CFG).chain("NIFTY", EXPIRY)
    chain.quotes = {k: replace(q, bid=None, ask=None) for k, q in chain.quotes.items()}
    return chain


class LiveQuotes(SampleProvider):
    """A provider whose chain has no book but whose live quote does (like Groww)."""

    def __init__(self, cfg, spread_pct=1.0, available=True):
        super().__init__(cfg)
        self.spread_pct, self.available, self.asked = spread_pct, available, []

    def chain(self, underlying, expiry):
        chain = super().chain(underlying, expiry)
        chain.quotes = {k: replace(q, bid=None, ask=None) for k, q in chain.quotes.items()}
        return chain

    def live_quote(self, chain, strike, kind):
        self.asked.append((strike, kind))
        if not self.available:
            return None
        leg = chain.get(strike, kind)
        half = leg.ltp * self.spread_pct / 200
        return replace(leg, bid=round(leg.ltp - half, 2), ask=round(leg.ltp + half, 2))


def picker(live_quotes):
    return ContractPicker(PickerRules(min_open_interest=0), ExitLevels(), CFG["position_rules"], 10_000, live_quotes)


def view():
    return MarketView("NIFTY", Direction.BULLISH, 0.6, 0.8, strong_evidence=True)


def test_entry_uses_the_live_ask_when_the_chain_has_no_book():
    quotes = LiveQuotes(CFG)
    idea, reason = picker(quotes).pick(view(), chain_without_book(), SESSION_DAY)
    assert idea, reason
    assert idea.fill_source == FILL_BID_ASK and len(quotes.asked) == 1
    live = quotes.live_quote(chain_without_book(), idea.strike, idea.option_kind)
    assert idea.entry_price == live.ask


def test_a_wide_live_spread_refuses_the_trade_and_says_why():
    idea, reason = picker(LiveQuotes(CFG, spread_pct=8.0)).pick(view(), chain_without_book(), SESSION_DAY)
    assert idea is None and reason == "live quote: wide bid-ask gap"


def test_no_live_quote_falls_back_to_last_price_and_records_it():
    idea, _ = picker(LiveQuotes(CFG, available=False)).pick(view(), chain_without_book(), SESSION_DAY)
    assert idea.fill_source == FILL_LAST_PRICE
    trades = []
    trade = journal.open_trade(trades, idea.to_journal_candidate(), CFG, lots=1)
    assert trade["fill_source"] == FILL_LAST_PRICE


def test_exits_are_priced_at_the_live_bid():
    quotes = LiveQuotes(CFG)
    idea, _ = picker(quotes).pick(view(), chain_without_book(), SESSION_DAY)
    trade = journal.open_trade([], idea.to_journal_candidate(), CFG, lots=1)
    value, orders, _ = journal.close_value(trade, quotes, slippage=0.5)
    live = quotes.live_quote(quotes.chain("NIFTY", EXPIRY), idea.strike, idea.option_kind)
    assert value == live.bid and orders == [("sell", live.bid)]
    assert trade["exit_fill_source"] == FILL_BID_ASK
    journal.close_value(trade, LiveQuotes(CFG, available=False), slippage=0.5)
    assert trade["exit_fill_source"] == FILL_LAST_PRICE


def test_groww_book_is_read_from_bid_offer_fields_or_market_depth():
    assert parse_groww_book({"bid_price": 101.5, "offer_price": 102.0}) == (101.5, 102.0)
    depth = {"depth": {"buy": [{"price": 99.0, "quantity": 75}], "sell": [{"price": 99.6, "quantity": 150}]}}
    assert parse_groww_book(depth) == (99.0, 99.6)
    assert parse_groww_book({}) == (None, None)
