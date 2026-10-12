from datetime import datetime, timedelta

import pytest
import requests

from fno.constants import EVENT_NEWS_SIGHTING, EVENT_NEWS_STORY, NEWS_THEME_WORLD
from fno.live.learning.news_speed import format_speed_report, source_speeds
from fno.live.news.api_sources import MarketauxNewsSource, indian_symbols
from fno.live.news.exchange_sources import parse_bse_announcements, parse_nse_announcements
from fno.live.news.models import NewsItem
from fno.live.news.poll_schedule import PollSchedule, SourcePlan
from fno.live.news.rss_source import RssFeedSource, parse_feed
from fno.live.news.source import NewsSource
from fno.live.news.story_book import StoryBook
from fno.live.news.tagging import SymbolTagger
from fno.live.news.watcher import NewsWatcher
from fno.live.results_store import JsonlResultsStore
from fno.models import IST

MARKET_TIME = datetime(2026, 10, 13, 10, 0, tzinfo=IST)  # a Tuesday, market open
EVENING = datetime(2026, 10, 13, 20, 0, tzinfo=IST)
NAMES = {
    "RELIANCE": "Reliance Industries Ltd.",
    "OIL": "Oil India Ltd.",
    "MEDANTA": "Global Health Ltd.",
    "TCS": "Tata Consultancy Services Ltd.",
}
RSS = """<rss><channel>
<item><title>Reliance shares jump &amp; hit record</title><link>https://x.com/a?utm=1</link>
<pubDate>Tue, 13 Oct 2026 09:58:00 +0530</pubDate><description>&lt;p&gt;Big day&lt;/p&gt;</description></item>
</channel></rss>"""


class FakeResponse:
    def __init__(self, status=200, text="", payload=None, headers=None):
        self.status_code, self.text, self._payload, self.headers = status, text, payload, headers or {}
        self.ok = status < 400

    def json(self):
        return self._payload

    def raise_for_status(self):
        if not self.ok:
            raise requests.HTTPError(f"HTTP {self.status_code} for url: https://x?api_token=SECRET")


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers or {}})
        return self.responses.pop(0)


def test_feed_parsing_unescapes_text():
    item = parse_feed(RSS, "ET")[0]
    assert item.title == "Reliance shares jump & hit record"
    assert item.summary == "Big day"
    assert item.published_at.hour == 9


def test_feed_asks_only_for_changes_and_respects_its_cache_time():
    first = FakeResponse(text=RSS, headers={"ETag": '"v1"', "Cache-Control": "public, max-age=90"})
    session = FakeSession([first, FakeResponse(status=304)])
    feed = RssFeedSource("ET", "https://feed", session)
    assert len(feed.fetch(MARKET_TIME)) == 1
    assert feed.min_interval_seconds == 90
    assert feed.fetch(MARKET_TIME) == []
    assert session.calls[1]["headers"]["If-None-Match"] == '"v1"'


def test_exchange_filings_are_parsed_with_their_symbol():
    nse = parse_nse_announcements(
        [
            {
                "symbol": "RELIANCE",
                "sm_name": "Reliance Industries",
                "desc": "Outcome of Board Meeting",
                "attchmntText": "Board approves fund raise",
                "sort_date": "2026-10-13 09:57:10",
            }
        ]
    )
    assert nse[0].symbols == ("RELIANCE",) and "fund raise" in nse[0].title and nse[0].published_at.minute == 57
    bse = parse_bse_announcements(
        {
            "Table": [
                {
                    "HEADLINE": "Order win",
                    "SLONGNAME": "Larsen & Toubro Ltd",
                    "NSURL": "https://www.bseindia.com/stock-share-price/larsen--toubro-ltd/lt/500510/",
                    "DissemDT": "2026-10-13T09:58:00",
                }
            ]
        }
    )
    assert bse[0].symbols == ("LT",) and bse[0].title.startswith("Larsen")


def test_marketaux_keeps_indian_symbols_and_never_shows_the_token_in_errors():
    assert indian_symbols([{"symbol": "RELIANCE.NS"}, {"symbol": "500325.BO"}, {"symbol": "AAPL"}]) == ("RELIANCE",)
    source = MarketauxNewsSource("SECRET", FakeSession([FakeResponse(status=429)]))
    with pytest.raises(requests.HTTPError) as err:
        source.fetch(MARKET_TIME)
    assert "SECRET" not in str(err.value)


def test_tagging_by_name_symbol_index_and_world_theme():
    tagger = SymbolTagger(NAMES)
    assert tagger.symbols("Reliance Industries posts record profit") == ("RELIANCE",)
    assert tagger.symbols("TCS wins deal; Bank Nifty slips") == ("TCS", "BANKNIFTY")
    assert tagger.symbols("Oil near $103 as global markets fall") == ()  # not Oil India, not Global Health
    assert tagger.themes("Houthis attack Saudi Arabia; crude jumps") == (NEWS_THEME_WORLD,)


def test_one_story_from_many_sources_measures_each_delay():
    book = StoryBook(SymbolTagger(NAMES))
    first = book.add(
        NewsItem("NSE filings", "Reliance Industries board approves Rs 20,000 crore fund raise"), MARKET_TIME
    )
    later = book.add(
        NewsItem("ET Markets", "Reliance Industries board approves Rs 20,000 crore fund raise via QIP"),
        MARKET_TIME + timedelta(seconds=150),
    )
    assert first.is_new and not later.is_new and later.lag_seconds == 150
    assert first.story.symbols == ("RELIANCE",)
    repeat = NewsItem("ET Markets", "Reliance Industries board approves Rs 20,000 crore fund raise via QIP")
    assert book.add(repeat, MARKET_TIME + timedelta(seconds=200)) is None


class ScriptedSource(NewsSource):
    min_interval_seconds = 0.0

    def __init__(self, name, answers):
        self.name, self.answers = name, list(answers)

    def fetch(self, now):
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def test_schedule_is_sequential_staggered_and_backs_off():
    a = SourcePlan(ScriptedSource("a", []), every_seconds=60)
    b = SourcePlan(ScriptedSource("b", []), every_seconds=60, daily_limit=1)
    schedule = PollSchedule([a, b], min_gap_seconds=5)
    schedule.start(MARKET_TIME)
    plan, at = schedule.next_request(MARKET_TIME)
    assert plan is a and at == MARKET_TIME
    schedule.record(a, MARKET_TIME, ok=True)
    plan, at = schedule.next_request(MARKET_TIME)
    assert plan is b and at == MARKET_TIME + timedelta(seconds=5)  # never two requests at once
    schedule.record(b, at, ok=False)
    assert b.next_due == at + timedelta(seconds=120)  # a failure doubles the wait
    assert schedule.next_request(at + timedelta(seconds=500))[0] is a  # b used its daily allowance
    assert schedule.interval(a, EVENING) == 300  # off hours: 5x slower
    a.source.min_interval_seconds = 480  # a feed whose cache lasts 8 minutes is never asked sooner
    assert schedule.interval(a, MARKET_TIME) == 480 and schedule.interval(a, EVENING) == 480


def test_watcher_reports_only_fresh_news_and_survives_failures(tmp_path):
    store = JsonlResultsStore(tmp_path)
    old = NewsItem("NSE filings", "Reliance Industries old filing about something", published_at=MARKET_TIME)
    fresh = NewsItem("NSE filings", "Reliance Industries board approves fund raise of Rs 20,000 crore")
    copy = NewsItem("ET Markets", "Reliance Industries board approves fund raise of Rs 20,000 crore today")
    nse = SourcePlan(ScriptedSource("NSE filings", [[old], [old, fresh]]), every_seconds=60)
    et = SourcePlan(ScriptedSource("ET Markets", [requests.ConnectionError("down"), [copy]]), every_seconds=60)
    watcher = NewsWatcher(PollSchedule([nse, et], 5), StoryBook(SymbolTagger(NAMES)), store)
    watcher.start(MARKET_TIME)
    assert watcher.poll(nse, MARKET_TIME) == []  # first answer = already published: baseline
    assert watcher.poll(et, MARKET_TIME) == [] and "ET Markets" in watcher.errors
    assert len(watcher.poll(nse, MARKET_TIME + timedelta(seconds=60))) == 1
    assert len(watcher.poll(et, MARKET_TIME + timedelta(seconds=90))) == 1 and not watcher.errors
    stories = store.payloads(EVENT_NEWS_STORY, MARKET_TIME.date())
    sightings = store.payloads(EVENT_NEWS_SIGHTING, MARKET_TIME.date())
    assert [s["source"] for s in stories] == ["NSE filings"] and sightings[0]["lag_seconds"] == 30
    speeds = source_speeds(stories, sightings)
    assert speeds[0].source == "NSE filings" and speeds[0].first == 1
    assert "0.5 min" in format_speed_report(speeds)

    restarted = NewsWatcher(PollSchedule([], 5), StoryBook(SymbolTagger(NAMES)), store)
    restarted.start(MARKET_TIME + timedelta(minutes=5))
    assert restarted.book.add(copy, MARKET_TIME + timedelta(minutes=6)) is None  # known before the restart
