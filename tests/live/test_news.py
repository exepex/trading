from datetime import datetime, timedelta

import pytest
import requests

from fno.constants import EVENT_NEWS_SIGHTING, EVENT_NEWS_STORY, NEWS_THEME_WORLD, NewsCredibility
from fno.live.learning.news_speed import format_speed_report, source_speeds
from fno.live.news.api_sources import MarketauxNewsSource, indian_symbols
from fno.live.news.exchange_sources import parse_bse_announcements, parse_nse_announcements
from fno.live.news.impact import NewsRoom
from fno.live.news.models import NewsItem
from fno.live.news.poll_schedule import ActiveWindow, PollSchedule, SourcePlan
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


def book():
    outlets = {"BS Markets": "Business Standard", "BS Companies": "Business Standard"}
    return StoryBook(SymbolTagger(NAMES), outlet_of=outlets, primary_sources=frozenset({"NSE filings"}))


def test_more_outlets_raise_credibility_and_one_outlet_repeating_is_a_duplicate():
    stories = book()
    first = stories.add(NewsItem("ET Markets", "Reliance Industries board approves fund raise via QIP"), MARKET_TIME)
    assert first.is_new and first.story.symbols == ("RELIANCE",)
    assert first.story.credibility is NewsCredibility.SINGLE_SOURCE
    later = stories.add(
        NewsItem("BS Markets", "Reliance Industries board approves QIP fund raise of Rs 20,000 crore"),
        MARKET_TIME + timedelta(seconds=150),
    )
    assert not later.is_new and later.lag_seconds == 150
    assert later.story.credibility is NewsCredibility.CORROBORATED
    same_paper = NewsItem("BS Companies", "Reliance Industries board clears fund raise via QIP route")
    assert stories.add(same_paper, MARKET_TIME + timedelta(seconds=200)) is None  # same newspaper, other feed
    filing = NewsItem("NSE filings", "Reliance Industries: board approves fund raise via QIP", symbols=("RELIANCE",))
    assert (
        stories.add(filing, MARKET_TIME + timedelta(seconds=210)).story.credibility is NewsCredibility.EXCHANGE_FILING
    )


def test_reworded_headlines_match_on_company_and_figures_but_other_companies_never_do():
    stories = book()
    stories.add(NewsItem("ET Markets", "Reliance to raise Rs 20,000 crore through QIP"), MARKET_TIME)
    reworded = NewsItem("Livemint", "Reliance Industries board okays Rs 20,000-crore share sale to institutions")
    assert not stories.add(reworded, MARKET_TIME + timedelta(minutes=1)).is_new
    other = NewsItem("Livemint", "TCS to raise Rs 20,000 crore through QIP")
    assert stories.add(other, MARKET_TIME + timedelta(minutes=2)).is_new


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
    schedule = PollSchedule([a, b], min_gap_seconds=5, window=ActiveWindow())
    schedule.start(MARKET_TIME)
    plan, at = schedule.next_request(MARKET_TIME)
    assert plan is a and at == MARKET_TIME
    schedule.record(a, MARKET_TIME, ok=True)
    plan, at = schedule.next_request(MARKET_TIME)
    assert plan is b and at == MARKET_TIME + timedelta(seconds=5)  # never two requests at once
    schedule.record(b, at, ok=False)
    assert b.next_due == at + timedelta(seconds=120)  # a failure doubles the wait
    assert schedule.next_request(at + timedelta(seconds=500))[0] is a  # b used its daily allowance
    a.source.min_interval_seconds = 480  # a feed whose cache lasts 8 minutes is never asked sooner
    assert schedule.interval(a, MARKET_TIME) == 480


def test_nothing_is_fetched_outside_indian_market_hours_or_on_holidays():
    holiday = MARKET_TIME.date() + timedelta(days=1)
    window = ActiveWindow(is_trading_day=lambda day: day.weekday() < 5 and day != holiday)
    schedule = PollSchedule([SourcePlan(ScriptedSource("a", []), every_seconds=60)], 5, window)
    plan, opens = schedule.next_request(EVENING)
    assert plan is None and opens == datetime(2026, 10, 15, 8, 45, tzinfo=IST)  # skips the holiday
    plan, at = schedule.next_request(opens)
    assert plan is not None and at == opens


def test_watcher_reports_only_fresh_news_and_survives_failures(tmp_path):
    store = JsonlResultsStore(tmp_path)
    old = NewsItem("NSE filings", "Reliance Industries old filing about something", published_at=MARKET_TIME)
    fresh = NewsItem("NSE filings", "Reliance Industries board approves fund raise of Rs 20,000 crore")
    copy = NewsItem("ET Markets", "Reliance Industries board approves fund raise of Rs 20,000 crore today")
    nse = SourcePlan(ScriptedSource("NSE filings", [[old], [old, fresh]]), every_seconds=60)
    et = SourcePlan(ScriptedSource("ET Markets", [requests.ConnectionError("down"), [copy]]), every_seconds=60)
    world = SourcePlan(
        ScriptedSource("BBC", [[], [NewsItem("BBC", "Houthis attack Saudi oil plant; crude jumps 6%")]]), 60
    )
    gossip = SourcePlan(ScriptedSource("Gossip", [[], [NewsItem("Gossip", "Ten tips for a happy retirement")]]), 60)
    watcher = NewsWatcher(
        PollSchedule([nse, et, world, gossip], 5),
        NewsRoom(StoryBook(SymbolTagger(NAMES))),
        store,
        frozenset({"RELIANCE"}),
    )
    watcher.start(MARKET_TIME)
    assert watcher.poll(nse, MARKET_TIME) == []  # first answer = already published: baseline
    assert watcher.poll(et, MARKET_TIME) == [] and "ET Markets" in watcher.errors
    assert len(watcher.poll(nse, MARKET_TIME + timedelta(seconds=60))) == 1
    assert len(watcher.poll(et, MARKET_TIME + timedelta(seconds=90))) == 1 and not watcher.errors
    for plan in (world, gossip):
        watcher.poll(plan, MARKET_TIME)
        watcher.poll(plan, MARKET_TIME + timedelta(seconds=100))  # world news is kept, gossip is not
    stories = store.payloads(EVENT_NEWS_STORY, MARKET_TIME.date())
    sightings = store.payloads(EVENT_NEWS_SIGHTING, MARKET_TIME.date())
    assert [s["source"] for s in stories] == ["NSE filings", "BBC"] and sightings[0]["lag_seconds"] == 30
    assert sightings[0]["credibility"] == NewsCredibility.CORROBORATED.value
    speeds = {s.source: s for s in source_speeds(stories, sightings)}
    assert speeds["NSE filings"].first == 1 and speeds["ET Markets"].later == 1
    assert "0.5 min" in format_speed_report(list(speeds.values()))

    restarted = NewsWatcher(
        PollSchedule([], 5), NewsRoom(StoryBook(SymbolTagger(NAMES))), store, frozenset({"RELIANCE"})
    )
    restarted.start(MARKET_TIME + timedelta(minutes=5))
    assert restarted.book.add(copy, MARKET_TIME + timedelta(minutes=6)) is None  # known before the restart
