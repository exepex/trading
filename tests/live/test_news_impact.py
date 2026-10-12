from datetime import datetime, timedelta

from fno.constants import NewsEventType
from fno.live.news.classifier import direction, event_type
from fno.live.news.impact import ImpactSettings, NewsRoom
from fno.live.news.models import NewsItem, Sighting, Story
from fno.live.news.story_book import StoryBook
from fno.live.news.tagging import SymbolTagger
from fno.live.signals.base import SymbolInputs
from fno.live.signals.news_signals import FastNews, NewsShockGuard
from fno.models import IST

NOW = datetime(2026, 10, 13, 11, 0, tzinfo=IST)
NAMES = {"RELIANCE": "Reliance Industries Ltd.", "WIPRO": "Wipro Ltd."}


def story(title, summary="", themes=(), sentiment=None):
    return Story("x", title, "", None, (), themes, summary, [Sighting("ET", NOW)], sentiment=sentiment)


def test_headlines_are_classified_like_a_desk_analyst_would():
    assert event_type(story("Wipro Q2 net profit rises 8%, beats estimates")) is NewsEventType.RESULTS
    assert event_type(story("SEBI bars promoter of XYZ from markets")) is NewsEventType.REGULATORY
    assert event_type(story("L&T bags Rs 5,000 crore order from NHAI")) is NewsEventType.ORDER
    assert event_type(story("Reliance: Certificate under Regulation 74(5)")) is NewsEventType.ROUTINE
    assert event_type(story("Crude jumps 6% after attack", themes=("WORLD",))) is NewsEventType.MACRO
    assert direction(story("Wipro Q2 net profit rises 8%, beats estimates")) > 0
    assert direction(story("Infosys shares plunge after guidance cut")) < 0
    assert direction(story("Crude oil jumps 6%")) < 0  # rising oil is bad for Indian markets
    assert direction(story("Board meeting on Friday")) == 0
    assert direction(story("anything", sentiment=0.4)) == 0.4  # a source's own score wins


def room_with(*items_and_minutes):
    room = NewsRoom(StoryBook(SymbolTagger(NAMES), primary_sources=frozenset({"NSE filings"})), ImpactSettings())
    for item, minutes_ago in items_and_minutes:
        room.book.add(item, NOW - timedelta(minutes=minutes_ago))
    return room


def inputs(symbol, room):
    return SymbolInputs(
        symbol=symbol, snapshot=None, candles=[], benchmark_change_pct=None, research=None, news=room.pulse(symbol, NOW)
    )


def test_fresh_credible_results_push_harder_than_old_rumours():
    filing = NewsItem("NSE filings", "Wipro Ltd: Q2 net profit rises 12%, beats estimates", symbols=("WIPRO",))
    rumour = NewsItem("Blog", "Wipro shares jump on takeover chatter")
    room = room_with((filing, 5))
    pulse = room.pulse("WIPRO", NOW)
    assert pulse.score > 0.8 and pulse.strongest.event is NewsEventType.RESULTS
    weak = room_with((rumour, 90)).pulse("WIPRO", NOW)
    assert 0 < weak.score < 0.1  # single source, an hour and a half old
    vote = FastNews(0.8).evaluate(inputs("WIPRO", room))
    assert vote.score > 0.8 and "results" in vote.reason


def test_world_news_moves_indices_more_than_single_stocks():
    war = NewsItem("BBC", "Missile attack on Saudi oil plant; markets fall")
    room = room_with((war, 2))
    assert room.pulse("NIFTY", NOW).score < room.pulse("WIPRO", NOW).score < 0


def test_guard_waits_after_credible_big_news_with_unclear_direction():
    meeting = NewsItem(
        "NSE filings", "Reliance Industries Ltd: Outcome of board meeting on fund raising", symbols=("RELIANCE",)
    )
    room = room_with((meeting, 3))
    assert NewsShockGuard({"quiet_minutes": 15, "min_weight": 0.5}).evaluate(inputs("RELIANCE", room)).blocked
    later = room_with((meeting, 30))
    assert not NewsShockGuard({"quiet_minutes": 15, "min_weight": 0.5}).evaluate(inputs("RELIANCE", later)).blocked
