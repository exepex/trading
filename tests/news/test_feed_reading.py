"""Story A19 criteria 1, 2 and 14: settings, time formats, parsing and the RSS adapter."""

from datetime import UTC, datetime

import pytest
import requests

from fno.config import load_app_config
from fno.news.fetch import RssFeedSource
from fno.news.identity import canonical_url, headline_key, item_id
from fno.news.names import DAY, HTTP_ERROR, NO_ITEMS, NOT_XML, SECOND
from fno.news.parse import FeedProblem, parse_feed
from fno.news.settings import NewsSettingsError, news_settings
from fno.news.times import TIME_FORMATS
from tests.news.fakes import MARKETS, RBI, SEBI, item_xml, rss

FORMATS = frozenset(TIME_FORMATS)
STORY_FEEDS = {  # the step-0 "In" table of docs/stories/A19-news-capture.md
    "et-markets": "publisher", "et-economy": "publisher", "mint-markets": "publisher", "mint-economy": "publisher",
    "businessline-markets": "publisher", "businessline-economy": "publisher", "rbi-press": "official",
    "sebi": "official",
}  # fmt: skip


def settings(**news):
    base = {"publisher_feeds": True, "active_window": {"start": "07:00", "end": "23:00"}, "overnight_bridge": False,
            "feeds": [{"id": "a", "publisher": "P", "kind": "publisher", "url": "https://a.example/rss",
                       "time_format": "rfc822", "stale_session_hours": 3, "stale_any_hours": 24}]}  # fmt: skip
    return news_settings({"news": {**base, **news}}, FORMATS)


def test_committed_feed_list_is_the_story_table_and_the_owner_window():
    configured = news_settings(load_app_config(), FORMATS)
    assert {f.id: f.kind for f in configured.feeds} == STORY_FEEDS
    assert (str(configured.window.start), str(configured.window.end)) == ("07:00:00", "23:00:00")
    assert configured.overnight_bridge is False  # owner's row 253 stands until the SF6 answer (judge 352 add. 2)
    sebi = next(f for f in configured.feeds if f.id == "sebi")
    assert sebi.excluded_paths == ("/legal/circulars/",)
    assert all(f.url.startswith("https://") for f in configured.feeds)


def test_publisher_switch_leaves_only_official_feeds():
    official = {**settings().feeds[0].__dict__, "id": "b", "kind": "official"}
    both = settings(feeds=[settings().feeds[0].__dict__ | {"excluded_paths": []}, official])
    assert [f.id for f in both.active_feeds()] == ["a", "b"]
    off = settings(publisher_feeds=False, feeds=[settings().feeds[0].__dict__, official])
    assert [f.id for f in off.active_feeds()] == ["b"]


@pytest.mark.parametrize(
    "change",
    [
        {"publisher_feeds": "yes"},
        {"overnight_bridge": None},
        {"active_window": {"start": "7am", "end": "23:00"}},
        {"feeds": []},
        {"feeds": [{"id": "a"}]},
    ],
)
def test_bad_settings_stop_with_a_named_error(change):
    with pytest.raises(NewsSettingsError):
        settings(**change)


@pytest.mark.parametrize(
    "field, value", [("kind", "blog"), ("time_format", "iso"), ("url", "http://a"), ("stale_any_hours", 0)]
)
def test_bad_feed_values_are_refused(field, value):
    feed = {**settings().feeds[0].__dict__, field: value}
    feed.pop("excluded_paths")
    with pytest.raises(NewsSettingsError):
        settings(feeds=[feed])


def test_missing_news_section_is_refused():
    with pytest.raises(NewsSettingsError):
        news_settings({}, FORMATS)


def test_duplicate_feed_ids_are_refused():
    feed = settings().feeds[0].__dict__
    with pytest.raises(NewsSettingsError):
        settings(feeds=[feed, feed])


@pytest.mark.parametrize(
    "fmt, raw, value, precision",
    [
        ("rfc822", "Fri, 16 Oct 2026 15:08:49 +0530", "2026-10-16T09:38:49+00:00", SECOND),
        ("rfc822", "Fri, 16 Oct 2026 03:41:38 GMT", "2026-10-16T03:41:38+00:00", SECOND),
        ("rfc822_ist", "Fri, 16 Oct 2026 15:00:00", "2026-10-16T09:30:00+00:00", SECOND),
        ("day_comma_year", "16 Oct, 2026 +0530", "2026-10-16", DAY),
    ],
)
def test_each_time_format_reads_its_step0_sample(fmt, raw, value, precision):
    read = TIME_FORMATS[fmt].read(raw)
    assert (read.raw, read.value, read.precision) == (raw, value, precision)


@pytest.mark.parametrize(
    "fmt, raw",
    [("rfc822", "16-Oct-2026 16:26:00"), ("rfc822", "Fri, 16 Oct 2026 15:00:00"), ("rfc822_ist", "x"),
     ("rfc822_ist", "Fri, 16 Oct 2026 15:00:00 +0530"), ("day_comma_year", "2026-10-16"), ("rfc822", "")],
)  # fmt: skip
def test_an_unreadable_time_stays_none_with_its_raw_text(fmt, raw):
    read = TIME_FORMATS[fmt].read(raw)
    assert (read.raw, read.value, read.precision) == (raw, None, None)


def test_parse_reads_items_as_plain_text():
    data = rss(
        item_xml("Fixture &amp; title", "https://a.example/x", "Fri, 16 Oct 2026 15:08:49 +0530", "<b>Bold</b> text")
    )
    [item] = parse_feed(data, MARKETS)
    assert (item.title, item.summary, item.url) == ("Fixture & title", "Bold text", "https://a.example/x")
    assert item.published.precision == SECOND


@pytest.mark.parametrize(
    "data, kind",
    [
        (b"<!DOCTYPE html><html><body>Access Denied</body></html>", NOT_XML),
        (b"  <html><body>maintenance</body></html>", NOT_XML),
        (b"<rss><channel><item>", NOT_XML),
        (rss(), NO_ITEMS),
        (rss("<item><title>no link</title></item>"), NO_ITEMS),
        (b"", NOT_XML),
    ],
)
def test_bad_answers_are_named_failures(data, kind):
    with pytest.raises(FeedProblem) as problem:
        parse_feed(data, MARKETS)
    assert problem.value.kind == kind


def test_sebi_circulars_are_never_returned():
    day = "16 Oct, 2026 +0530"
    order = item_xml("Order", "https://www.sebi.gov.in/enforcement/orders/oct-2026/x.html", day)
    circular = item_xml("Circular", "https://www.sebi.gov.in/legal/circulars/oct-2026/y.html", day)
    data = rss(order, circular)
    assert [i.title for i in parse_feed(data, SEBI)] == ["Order"]


def test_canonical_url_drops_tracking_keeps_ids():
    assert canonical_url("HTTPS://WWW.A.example/x/?utm_source=rss&utm_medium=feed#top") == "https://www.a.example/x"
    rbi = "https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=63818"
    assert canonical_url(rbi + "&utm_campaign=z") == rbi
    assert item_id(rbi) != item_id(rbi.replace("63818", "63819"))
    assert canonical_url("https://a.example/") == "https://a.example"


def test_headline_key_ignores_case_and_punctuation():
    assert headline_key("RBI keeps repo-rate at 5.5%!") == headline_key("rbi keeps repo rate at 5 5")
    assert headline_key("...") == ""


class Response:
    def __init__(self, status, content=b"", headers=None):
        self.status_code, self.content, self.headers = status, content, headers or {}


class Session:
    def __init__(self, *answers):
        self.answers, self.sent = list(answers), []

    def get(self, url, headers=None, timeout=None):
        self.sent.append(headers)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def clock():
    return datetime(2026, 10, 16, 10, 0, tzinfo=UTC)


def test_rss_source_sends_conditional_headers_and_reads_304():
    first = Response(200, b"<rss/>", {"ETag": '"abc"', "Last-Modified": "Fri, 16 Oct 2026 10:41:04 GMT",
                                      "Date": "Fri, 16 Oct 2026 10:00:02 GMT"})  # fmt: skip
    session = Session(first, Response(304))
    source = RssFeedSource(RBI, clock, session)
    fetched = source.fetch()
    assert (fetched.status, fetched.data, fetched.server_date.second) == (200, b"<rss/>", 2)
    assert source.fetch().not_modified
    assert session.sent[1]["If-None-Match"] == '"abc"'
    assert session.sent[1]["If-Modified-Since"] == "Fri, 16 Oct 2026 10:41:04 GMT"
    assert "If-None-Match" not in session.sent[0]


@pytest.mark.parametrize("answer", [Response(503), Response(404), requests.ConnectionError("down")])
def test_rss_source_failures_are_http_errors(answer):
    with pytest.raises(FeedProblem) as problem:
        RssFeedSource(RBI, clock, Session(answer)).fetch()
    assert problem.value.kind == HTTP_ERROR


def test_an_item_with_a_broken_link_is_skipped_never_a_crash():
    good = item_xml("Fine", "https://a.example/fine", "Fri, 16 Oct 2026 15:08:49 +0530")
    broken = item_xml("Broken", "http://[abc/x", "Fri, 16 Oct 2026 15:08:49 +0530")
    assert [i.title for i in parse_feed(rss(good, broken), MARKETS)] == ["Fine"]


def test_a_cached_answer_has_no_server_date():
    cached = Response(200, b"<rss/>", {"Date": "Fri, 16 Oct 2026 09:50:00 GMT", "Age": "459"})
    assert RssFeedSource(RBI, clock, Session(cached)).fetch().server_date is None
    fresh = Response(200, b"<rss/>", {"Date": "Fri, 16 Oct 2026 09:59:59 GMT", "Age": "0"})
    assert RssFeedSource(RBI, clock, Session(fresh)).fetch().server_date is not None
