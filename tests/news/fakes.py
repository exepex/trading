"""Fakes and fixtures for story A19's tests. The feeds are trimmed from 16 Oct 2026's real answers (their structure
and date formats), with every headline, summary and link replaced by neutral text, so no publisher text enters this
public repository."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from fno.alerts.sender import SENT, AlertSender
from fno.models import IST
from fno.news.episodes import EpisodeLog, LogRow
from fno.news.fetch import FeedFetch, NewsSource
from fno.news.settings import Feed
from fno.research_data.calendar import CsvSessionCalendar

HEADLINE = "Fixture headline seventeen alpha"  # grepped for in printed lines and committed files (criterion 5)
LINK = "https://news.example.in/markets/fixture-story-17"

MARKETS = Feed("et-markets", "Economic Times", "publisher", "https://economictimes.indiatimes.com/markets/rss.cms",
               "rfc822", 3, 24)  # fmt: skip
MINT = Feed("mint-markets", "Mint", "publisher", "https://www.livemint.com/rss/markets", "rfc822", 3, 24)
RBI = Feed("rbi-press", "Reserve Bank of India", "official", "https://www.rbi.org.in/pressreleases_rss.xml",
           "rfc822_ist", 24, 96)  # fmt: skip
SEBI = Feed("sebi", "SEBI", "official", "https://www.sebi.gov.in/sebirss.xml", "day_comma_year", 24, 120,
            ("/legal/circulars/",))  # fmt: skip


def ist(*args) -> datetime:
    return datetime(*args, tzinfo=IST)


def item_xml(title: str, link: str, pub: str, description: str = "Neutral fixture summary") -> str:
    return (f"<item><title>{title}</title><description><![CDATA[<p>{description}</p>]]></description>"
            f"<link>{link}</link><guid>{link}</guid><pubDate>{pub}</pubDate></item>")  # fmt: skip


def rss(*items: str) -> bytes:
    return ('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Fixture</title>'
            + "".join(items) + "</channel></rss>").encode("utf-8")  # fmt: skip


def calendar() -> CsvSessionCalendar:
    """NSE 2026 with one weekday holiday (Diwali Balipratipada, 10 Nov 2026) and no special session."""
    rows = (
        "date,kind,description,source_url\n2026-11-10,holiday,Diwali Balipratipada,https://www.nseindia.com/fixture\n"
    )
    return CsvSessionCalendar(rows)


class Clock:
    def __init__(self, start: datetime):
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


class Alerts(AlertSender):
    def __init__(self, outcome: str = SENT):
        self.sent, self.outcome = [], outcome

    def send(self, text: str) -> str:
        self.sent.append(text)
        return self.outcome


class MemoryLog(EpisodeLog):
    def __init__(self, rows: list[LogRow] | None = None):
        self._rows = list(rows or [])
        self.messages: list[str] = []

    def rows(self) -> list[LogRow]:
        return list(self._rows)

    def append(self, day: date, step: str, kind: str, message: str) -> None:
        self._rows.append(LogRow(day, "news-capture", step, kind))
        self.messages.append(message)


class ScriptedSource(NewsSource):
    """Answers from a list, one per fetch (the last repeats); an exception in the list is raised, None is a 304."""

    def __init__(self, feed: Feed, answers: list, clock: Clock, server_offset: timedelta = timedelta(0)):
        self.feed, self.answers, self.clock, self.offset = feed, list(answers), clock, server_offset
        self.calls = 0

    def fetch(self) -> FeedFetch:
        answer = self.answers[min(self.calls, len(self.answers) - 1)]
        self.calls += 1
        if isinstance(answer, Exception):
            raise answer
        status, data = (304, b"") if answer is None else (200, answer)
        now = self.clock()
        return FeedFetch(status, data, (now - self.offset).astimezone(UTC), now, now)


class Committer:
    def __init__(self, outcome: str = "news receipts committed and pushed (1 file(s))"):
        self.outcome, self.calls = outcome, 0

    def commit(self, what: str) -> str:
        self.calls += 1
        return self.outcome
