"""Regression tests for the judge's wave 0 news findings (3, 4, 5, 6, 7, 12)."""

import threading
from datetime import datetime, timedelta

import pytest
import requests

from fno.constants import NewsCredibility
from fno.live.news.api_sources import MarketauxNewsSource
from fno.live.news.classifier import direction
from fno.live.news.impact import NewsRoom
from fno.live.news.models import NewsItem, Sighting, Story
from fno.live.news.poll_schedule import ActiveWindow, PollSchedule, SourcePlan
from fno.live.news.source import NewsSource
from fno.live.news.story_book import StoryBook, outlet_domain
from fno.live.news.tagging import SymbolTagger
from fno.live.news.watcher import NewsWatcher
from fno.live.results_store import JsonlResultsStore
from fno.models import IST

NOW = datetime(2026, 10, 13, 11, 0, tzinfo=IST)


class Raising:
    def get(self, *args, **kwargs):
        raise requests.ConnectionError("HTTPSConnectionPool: url=/v1/news/all?api_token=SECRET_TOKEN_123")


def test_the_marketaux_token_never_appears_in_connection_errors():
    with pytest.raises(requests.RequestException) as err:
        MarketauxNewsSource("SECRET_TOKEN_123", Raising()).fetch(NOW)
    assert "SECRET_TOKEN_123" not in str(err.value) and "ConnectionError" in str(err.value)


@pytest.mark.parametrize(
    "headline, sign",
    [
        ("Sensex falls amid global turmoil", -1),
        ("Oil India shares jump on record profit", 1),
        ("Nifty slides as crude oil surges", -1),
        ("Markets gain as oil prices fall", 1),
        ("Rupee falls against dollar", -1),
        ("Infosys wins software deal", 1),
        ("Adani Enterprises shares slump 5%", -1),
        ("Dollar steady, Sensex rises 500 points", 1),
        ("US yields ease, Nifty gains 1%", 1),
        ("Crude oil steady as Sensex rallies", 1),
        ("Yields steady as Nifty falls", -1),
        ("Brent flat, Nifty climbs to record high", 1),
        ("Crude jumps 4% after attack on Saudi plant", -1),
        ("Rupee hits record low against dollar", -1),
        ("Rupee hits lowest level in a year", -1),
        ("Rupee hits weakest level since 2013", -1),
        ("Rupee hits the lowest level ever", -1),
        ("Rupee hits 3-week high after lows", 1),
        ("Rupee hits record low on strong dollar", -1),
        ("Rupee weakens on strong dollar demand", -1),
        ("Rupee rises 5 paise to 83.12 against US dollar despite firm dollar", 1),
        ("Rupee set to open higher as dollar strength eases", 1),
        ("TCS reports strong dollar revenue growth", 1),
        ("Rupee gains on strong dollar inflows", 1),
        ("Rupee hits peak after record lows", 1),
        ("Rupee hits strongest since lows of 2023", 1),
        ("Crude up 3% on supply fears", -1),
        ("Rupee down 20 paise against dollar", -1),
        ("US yields rise to 16-year high", -1),
        ("Dollar index jumps to two-year high", -1),
        ("Rupee recovers from record low", 1),
        ("Oil prices jump 3%", -1),
        ("Rupee gains against dollar", 1),
        ("Bond yields climb; banks fall", -1),
        ("Rupee hits one-year peak against dollar", 1),
        ("Rupee hits highest level since May", 1),
        ("Rupee hits strongest level in a year", 1),
        ("Rupee hits record high against dollar", 1),
        ("Rupee hits three-month high on FII inflows", 1),
    ],
)
def test_headline_direction(headline, sign):
    story = Story("x", headline, "", None, (), (), "", [Sighting("s", NOW)])
    assert direction(story) * sign > 0


@pytest.mark.parametrize(
    "headline",
    [
        "Crude falls after Sensex lows",
        "Rupee rises after market lows",
        "Rupee hits back from lowest levels",
        "Rupee hits importers with lowest margins",
        "Rupee hits 88 per dollar",
    ],
)
def test_rupee_hits_without_a_level_says_nothing(headline):
    assert direction(Story("x", headline, "", None, (), (), "", [Sighting("s", NOW)])) == 0


def test_a_re_served_article_is_one_outlet_and_other_publishers_corroborate_it():
    assert outlet_domain("https://economictimes.indiatimes.com/markets/x") == "indiatimes.com"
    assert outlet_domain("https://www.bbc.co.uk/news/articles/y") == "bbc.co.uk"
    book = StoryBook(SymbolTagger({}))
    url = "https://economictimes.indiatimes.com/markets/stocks/news/sebi-probe-into-xyz/articleshow/1.cms"
    title = "SEBI orders probe into XYZ trading, Nifty falls"
    book.add(NewsItem("ET Markets", title, url), NOW)
    for aggregator in ("Marketaux", "Finnhub", "AskNews"):
        assert book.add(NewsItem(aggregator, title, url), NOW) is None  # same article: not a confirmation
    assert book.stories[0].credibility is NewsCredibility.SINGLE_SOURCE
    other = book.add(NewsItem("Livemint Markets", title + " sharply", "https://www.livemint.com/market/a"), NOW)
    assert other.story.credibility is NewsCredibility.CORROBORATED


def test_big_unclear_world_news_pauses_index_entries_but_not_single_stocks():
    room = NewsRoom(StoryBook(SymbolTagger({})))
    for source, url in (("BBC Business", "https://www.bbc.co.uk/a"), ("Livemint", "https://www.livemint.com/b")):
        room.book.add(NewsItem(source, "Fed to announce interest rate decision tonight; oil in focus", url), NOW)
    assert room.pulse("NIFTY", NOW + timedelta(minutes=2)).major_unclear(15, 0.45) is not None
    assert room.pulse("TCS", NOW + timedelta(minutes=2)).major_unclear(15, 0.45) is None


class Flaky(NewsSource):
    name, min_interval_seconds = "Flaky", 0.0

    def __init__(self):
        self.calls = 0

    def fetch(self, now):
        self.calls += 1
        if self.calls == 1:
            return [{"datetime": "not a number"}]  # a malformed answer that breaks parsing downstream
        raise TypeError("unexpected payload")


def test_the_watcher_survives_unexpected_errors_and_keeps_polling(tmp_path):
    clock = {"now": NOW}
    plan = SourcePlan(Flaky(), every_seconds=1)
    schedule = PollSchedule([plan], 0.01, ActiveWindow(is_trading_day=lambda d: True))
    watcher = NewsWatcher(
        schedule, NewsRoom(StoryBook(SymbolTagger({}))), JsonlResultsStore(tmp_path), None, clock=lambda: clock["now"]
    )
    watcher.poll(plan, NOW)
    watcher.poll(plan, NOW)
    assert plan.failures == 1 and "Flaky" in watcher.errors
    stop = threading.Event()
    thread = threading.Thread(target=watcher.run_forever, args=(stop,), daemon=True)
    thread.start()
    thread.join(0.3)
    assert thread.is_alive()  # still running after errors
    stop.set()
    thread.join(2)


def test_daily_allowances_survive_a_restart(tmp_path):
    usage = tmp_path / "news_usage.json"

    class Quiet(NewsSource):
        name, min_interval_seconds = "AskNews", 0.0

        def fetch(self, now):
            return []

    first = PollSchedule([SourcePlan(Quiet(), 60, daily_limit=2)], 5, usage_file=usage)
    for minute in (0, 1):
        first.record(first.plans[0], NOW + timedelta(minutes=minute), ok=True)
    restarted = PollSchedule([SourcePlan(Quiet(), 60, daily_limit=2)], 5, usage_file=usage)
    restarted.start(NOW)
    assert restarted.next_request(NOW + timedelta(minutes=5))[0] is None  # allowance already used today


def test_a_damaged_usage_file_only_resets_that_source(tmp_path):
    usage = tmp_path / "news_usage.json"
    usage.write_text('{"AskNews": "x", "Marketaux": ["2026-10-13", 7]}')

    class Quiet(NewsSource):
        min_interval_seconds = 0.0

        def __init__(self, name):
            self.name = name

        def fetch(self, now):
            return []

    schedule = PollSchedule(
        [SourcePlan(Quiet("AskNews"), 60, 5), SourcePlan(Quiet("Marketaux"), 60, 95)], 5, usage_file=usage
    )
    assert schedule.plans[0].used_today == 0 and schedule.plans[1].used_today == 7


def test_prioritise_never_breaks_a_limit():
    class Quiet(NewsSource):
        min_interval_seconds = 0.0

        def __init__(self, name):
            self.name = name

        def fetch(self, now):
            return []

    healthy, failing, refused = (SourcePlan(Quiet(n), 300) for n in ("Marketaux", "NSE filings", "BSE filings"))
    schedule = PollSchedule([healthy, failing, refused], 5, ActiveWindow(is_trading_day=lambda d: True))
    schedule.record(healthy, NOW, ok=True)
    schedule.record(failing, NOW, ok=False)
    schedule.record(refused, NOW, ok=True, pause_seconds=900)
    before = (failing.next_due, refused.next_due)
    schedule.prioritise({"Marketaux", "NSE filings", "BSE filings"}, NOW + timedelta(seconds=10))
    assert healthy.next_due == NOW + timedelta(seconds=60)  # sooner than 300 s, never sooner than a minute
    assert (failing.next_due, refused.next_due) == before  # back-off and refusal pauses untouched
    schedule.prioritise({"Marketaux"}, NOW + timedelta(seconds=120))
    assert healthy.next_due == NOW + timedelta(seconds=60)  # never moved later either
