"""Story A19 criteria 3, 8 and 11: one row and one alert per failure episode, recovery, restarts, and each poll's
heartbeat, item lines, failures and clock check."""

from datetime import date, timedelta

import pytest

from fno.news.episodes import Episodes, LogRow
from fno.news.memory import SeenMemory
from fno.news.parse import FeedProblem
from fno.news.polling import FeedPoller
from fno.news.stale import StaleRule
from tests.news.fakes import (
    HEADLINE,
    LINK,
    MARKETS,
    RBI,
    Alerts,
    Clock,
    MemoryLog,
    ScriptedSource,
    calendar,
    ist,
    item_xml,
    rss,
)

T0 = ist(2026, 10, 16, 10, 0)


def episodes(rows=None, outcome="alert sent to #fno-desk"):
    clock, log, alerts, printed = Clock(T0), MemoryLog(rows), Alerts(outcome), []
    return Episodes(log, alerts, clock, printed.append), clock, log, alerts, printed


def test_first_failure_opens_one_row_and_one_alert_repeats_add_nothing_recovery_one_each():
    found, clock, log, alerts, _ = episodes()
    found.fail("et-markets", "http_error", "et-markets: HTTP 503")
    clock.sleep(600)
    found.fail("et-markets", "http_error", "et-markets: HTTP 503")
    assert (len(log.rows()), len(alerts.sent)) == (1, 1)
    clock.sleep(300)
    found.ok("et-markets")
    assert [r.kind for r in log.rows()] == ["http_error", "http_error_recovered"]
    assert "15 min, 2 failed poll(s)" in alerts.sent[-1]
    found.ok("et-markets")
    assert len(log.rows()) == 2


def test_a_restart_with_an_open_episode_adds_no_row_and_no_alert():
    open_row = LogRow(date(2026, 10, 16), "news-capture", "et-markets", "stale")
    found, _, log, alerts, _ = episodes([open_row])
    found.fail("et-markets", "stale", "again")
    assert (len(log.messages), alerts.sent) == (0, [])
    found.ok("et-markets", ("stale",))
    assert log.rows()[-1].kind == "stale_recovered" and "before this run" in alerts.sent[0]


def test_closed_episodes_and_other_jobs_and_events_are_not_open():
    rows = [LogRow(date(2026, 10, 15), "news-capture", "sebi", "no_items"),
            LogRow(date(2026, 10, 15), "news-capture", "sebi", "no_items_recovered"),
            LogRow(date(2026, 10, 15), "nse-margins", "sebi", "no_items"),
            LogRow(date(2026, 10, 15), "news-capture", "coverage_gap", "coverage_gap")]  # fmt: skip
    found, *_ = episodes(rows)
    assert found.open == {}


def test_alert_not_sent_is_named_in_the_row():
    found, _, log, _, printed = episodes(outcome="alert NOT sent: FNO_SLACK_BOT_TOKEN is not set")
    found.event("coverage_gap", "coverage_gap", "gap")
    assert log.messages[0].endswith("alert NOT sent: FNO_SLACK_BOT_TOKEN is not set")
    assert "alert NOT sent" in printed[0]


def poller(sources, clock, memory=None):
    found = Episodes(MemoryLog(), Alerts(), clock, lambda _: None)
    return FeedPoller(sources, memory or SeenMemory(), found, StaleRule(calendar()), "run-1"), found


PUB = "Fri, 16 Oct 2026 09:59:00 +0530"
FEED = rss(item_xml(HEADLINE, LINK, PUB))


def test_a_poll_gives_its_heartbeat_then_its_new_items_with_every_field():
    clock = Clock(T0)
    feeds, found = poller([ScriptedSource(MARKETS, [FEED], clock)], clock)
    heartbeat, line = feeds.poll(T0)
    assert heartbeat["line"] == "poll" and heartbeat["feeds"]["et-markets"] == {"outcome": "new", "listed": 1, "new": 1}
    assert line["line"] == "item" and line["first_seen_at"] == T0.isoformat()
    assert (line["previous_poll_at"], line["bootstrap"], line["published_precision"]) == (None, True, "second")
    expected = {"item_id", "version", "publisher", "feed", "url", "title", "summary", "published_raw", "line",
                "published_at", "published_precision", "first_seen_at", "previous_poll_at", "server_date",
                "clock_skew_s", "run_id", "same_headline_as", "bootstrap", "beyond_window", "new_item"}  # fmt: skip
    assert set(line) == expected
    clock.sleep(300)
    [again] = feeds.poll(clock())
    assert again["feeds"]["et-markets"]["outcome"] == "nothing_new"


def test_previous_poll_comes_from_the_heartbeat():
    clock = Clock(T0)
    second = rss(item_xml(HEADLINE, LINK, PUB), item_xml("Other fixture", LINK + "-2", PUB))
    feeds, _ = poller([ScriptedSource(MARKETS, [FEED, None, second], clock)], clock)
    feeds.poll(T0)
    clock.sleep(300)
    assert feeds.poll(clock())[0]["feeds"]["et-markets"]["outcome"] == "not_modified"
    clock.sleep(300)
    _, line = feeds.poll(clock())
    assert line["previous_poll_at"] == (T0 + timedelta(minutes=5)).isoformat()


def test_a_failed_feed_is_named_in_the_heartbeat_and_opens_an_episode():
    clock = Clock(T0)
    feeds, found = poller([ScriptedSource(RBI, [FeedProblem("http_error", "HTTP 503")], clock),
                           ScriptedSource(MARKETS, [FEED], clock)], clock)  # fmt: skip
    heartbeat, _ = feeds.poll(T0)
    assert heartbeat["feeds"]["rbi-press"]["outcome"] == "failed:http_error"
    assert found.is_open("rbi-press", "http_error")


def test_items_without_any_readable_time_are_kept_and_flagged():
    clock = Clock(T0)
    feeds, found = poller(
        [ScriptedSource(MARKETS, [rss(item_xml(HEADLINE, LINK, "16-Oct-2026 16:26:00"))], clock)], clock
    )
    _, line = feeds.poll(T0)
    assert line["published_at"] is None and found.is_open("et-markets", "no_times")


@pytest.mark.parametrize("offset, flagged", [(timedelta(seconds=5), False), (timedelta(seconds=5.1), True)])
def test_clock_skew_over_5_seconds_is_a_failure(offset, flagged):
    clock = Clock(T0)
    feeds, found = poller([ScriptedSource(MARKETS, [FEED], clock, offset)], clock)
    _, line = feeds.poll(T0)
    assert line["clock_skew_s"] == round(offset.total_seconds(), 1)
    assert found.is_open("clock", "clock") is flagged


def test_a_stale_feed_opens_an_episode_and_recovers_on_a_new_item():
    clock = Clock(T0)
    later = rss(item_xml(HEADLINE, LINK, PUB), item_xml("Fresh fixture", LINK + "-fresh", PUB))
    feeds, found = poller([ScriptedSource(MARKETS, [FEED, FEED, later], clock)], clock)
    feeds.poll(T0)
    clock.sleep(3 * 3600 + 60)
    feeds.poll(clock())
    assert found.is_open("et-markets", "stale")
    feeds.poll(clock())
    assert not found.is_open("et-markets", "stale")


def test_nothing_of_an_item_is_printed():
    clock, printed = Clock(T0), []
    found = Episodes(MemoryLog(), Alerts(), clock, printed.append)
    sources = [ScriptedSource(MARKETS, [FEED, FeedProblem("not_xml", "the answer is a web page, not a feed")], clock)]
    feeds = FeedPoller(sources, SeenMemory(), found, StaleRule(calendar()), "r")
    feeds.poll(T0)
    feeds.poll(T0 + timedelta(minutes=5))
    assert printed and all(HEADLINE not in p and LINK not in p for p in printed)
