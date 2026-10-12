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

    def __init__(self, cfg, spread_pct=1.0, available=True, raises=False, with_book=False, spot_shift_pct=0.0):
        super().__init__(cfg, spot_shift_pct=spot_shift_pct)
        self.spread_pct, self.available, self.raises, self.with_book, self.asked = (
            spread_pct,
            available,
            raises,
            with_book,
            [],
        )

    def chain(self, underlying, expiry):
        chain = super().chain(underlying, expiry)
        if not self.with_book:
            chain.quotes = {k: replace(q, bid=None, ask=None) for k, q in chain.quotes.items()}
        return chain

    def live_quote(self, chain, strike, kind):
        self.asked.append((strike, kind))
        if self.raises:
            raise ConnectionError("groww 429")
        if not self.available:
            return None
        leg = chain.get(strike, kind)
        half = leg.ltp * self.spread_pct / 200
        return replace(leg, bid=round(leg.ltp - half, 2), ask=round(leg.ltp + half, 2))


def picker(live_quotes, require_bid_ask=True):
    rules = PickerRules(min_open_interest=0, require_bid_ask=require_bid_ask)
    return ContractPicker(rules, ExitLevels(), CFG["position_rules"], 10_000, live_quotes)


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


def test_no_live_bid_ask_means_no_purchase_unless_allowed():
    for broken in (LiveQuotes(CFG, available=False), LiveQuotes(CFG, raises=True)):
        idea, reason = picker(broken).pick(view(), chain_without_book(), SESSION_DAY)
        assert idea is None and ("no live bid/ask" in reason or "live quote failed" in reason)
    idea, _ = picker(LiveQuotes(CFG, available=False), require_bid_ask=False).pick(
        view(), chain_without_book(), SESSION_DAY
    )
    assert idea.fill_source == FILL_LAST_PRICE
    trade = journal.open_trade([], idea.to_journal_candidate(), CFG, lots=1)
    assert trade["fill_source"] == FILL_LAST_PRICE


def test_a_chain_with_its_own_book_is_used_as_is():
    quotes = LiveQuotes(CFG, with_book=True)
    chain = quotes.chain("NIFTY", EXPIRY)
    idea, _ = picker(quotes).pick(view(), chain, SESSION_DAY)
    assert idea.fill_source == FILL_BID_ASK and idea.entry_price == chain.get(idea.strike, idea.option_kind).ask
    trade = journal.open_trade([], idea.to_journal_candidate(), CFG, lots=1)
    price = journal.price_to_close(trade, quotes, slippage=0.5)
    assert price.fill_source == FILL_BID_ASK and price.value == chain.get(idea.strike, idea.option_kind).bid
    assert quotes.asked == []  # the live quote is never asked for


def test_exits_are_priced_at_the_live_bid_and_say_so_only_when_closed():
    quotes = LiveQuotes(CFG)
    idea, _ = picker(quotes).pick(view(), chain_without_book(), SESSION_DAY)
    trade = journal.open_trade([], idea.to_journal_candidate(), CFG, lots=1)
    price = journal.price_to_close(trade, quotes, slippage=0.5)
    live = quotes.live_quote(quotes.chain("NIFTY", EXPIRY), idea.strike, idea.option_kind)
    assert price.value == live.bid and price.orders == [("sell", live.bid)] and price.fill_source == FILL_BID_ASK
    assert "exit_fill_source" not in trade  # nothing written while the trade is open
    journal.finalise_trade(trade, journal.price_to_close(trade, LiveQuotes(CFG, raises=True), 0.5), "manual", CFG)
    assert trade["exit_fill_source"] == FILL_LAST_PRICE  # a failed quote falls back, and says so


def test_groww_book_is_read_from_bid_offer_fields_or_market_depth():
    assert parse_groww_book({"bid_price": 101.5, "offer_price": 102.0}) == (101.5, 102.0)
    depth = {"depth": {"buy": [{"price": 99.0, "quantity": 75}], "sell": [{"price": 99.6, "quantity": 150}]}}
    assert parse_groww_book(depth) == (99.0, 99.6)
    assert parse_groww_book({}) == (None, None)


def desk_with_open_call(tmp_path, market):
    from fno.live.exit_policy import ExitPolicy
    from fno.live.market_clock import MarketClock, SessionTimes
    from fno.live.paper_desk import PaperDesk

    clock = MarketClock(SessionTimes.from_config(CFG["holding"], 15))
    desk = PaperDesk(tmp_path / "live.json", CFG, market, ExitPolicy(clock, 2, 1))
    idea, reason = picker(LiveQuotes(CFG)).pick(view(), chain_without_book(), SESSION_DAY)
    assert idea, reason
    return desk, desk.open(replace(idea, lots=1))


def test_a_failing_live_quote_never_stops_a_stop_loss_kill_switch_or_trim(tmp_path):
    from fno.constants import ExitReason, SessionPhase

    from .fakes import at

    crashed = LiveQuotes(CFG, raises=True, spot_shift_pct=-6.0)  # the call collapses; Groww's quote call fails
    desk, trade = desk_with_open_call(tmp_path, crashed)
    closed, errors = desk.review_open_trades(at(11, 0), SessionPhase.TRADING)
    assert [t["exit_reason"] for t in closed] == [ExitReason.STOP_LOSS.value] and errors == []
    assert desk.trades()[0]["exit_fill_source"] == FILL_LAST_PRICE

    desk, trade = desk_with_open_call(tmp_path / "k", LiveQuotes(CFG, raises=True))
    assert [t["id"] for t in desk.close_all(ExitReason.KILL_SWITCH)] == [trade["id"]]
    assert desk.open_trades() == []

    tight = dict(CFG, account={**CFG["account"], "max_overnight_premium": 0})
    desk, trade = desk_with_open_call(tmp_path / "t", LiveQuotes(CFG, raises=True))
    desk.cfg = tight
    closed, _ = desk.review_open_trades(at(15, 16), SessionPhase.SQUARE_OFF)
    assert any(t["exit_reason"] == ExitReason.OVERNIGHT_LIMIT.value for t in closed) and desk.open_trades() == []
