"""A publisher's RSS feed, asked politely: "anything new since last time?" and never faster than its own cache time."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

import requests

from .models import NewsItem
from .source import NewsSource

HEADER_ETAG = "ETag"
HEADER_LAST_MODIFIED = "Last-Modified"
HEADER_CACHE_CONTROL = "Cache-Control"
NOT_MODIFIED = 304
MAX_AGE_PATTERN = re.compile(r"max-age=(\d+)")
ATOM_NS = "{http://www.w3.org/2005/Atom}"
TAG_PATTERN = re.compile(r"<[^>]+>")
REQUEST_TIMEOUT_SECONDS = 20


def _text(element: ET.Element | None) -> str:
    raw = (element.text or "") if element is not None else ""
    return html.unescape(TAG_PATTERN.sub("", raw)).strip()


def _date(text: str) -> datetime | None:
    if not text:
        return None
    try:
        return parsedate_to_datetime(text)
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None


def parse_feed(xml_text: str, source: str) -> list[NewsItem]:
    """RSS 2.0 items or Atom entries as NewsItems."""
    root = ET.fromstring(xml_text)
    items = []
    for node in root.iter("item"):
        items.append(
            NewsItem(
                source=source,
                title=_text(node.find("title")),
                url=_text(node.find("link")),
                published_at=_date(_text(node.find("pubDate"))),
                summary=_text(node.find("description")),
            )
        )
    for node in root.iter(f"{ATOM_NS}entry"):
        link = node.find(f"{ATOM_NS}link")
        items.append(
            NewsItem(
                source=source,
                title=_text(node.find(f"{ATOM_NS}title")),
                url=link.get("href", "") if link is not None else "",
                published_at=_date(_text(node.find(f"{ATOM_NS}updated"))),
                summary=_text(node.find(f"{ATOM_NS}summary")),
            )
        )
    return [item for item in items if item.title]


class RssFeedSource(NewsSource):
    def __init__(self, name: str, url: str, session: requests.Session):
        self.name = name
        self.url = url
        self.session = session
        self._validators: dict[str, str] = {}
        self._max_age = 0.0

    @property
    def min_interval_seconds(self) -> float:
        return self._max_age

    def fetch(self, now: datetime) -> list[NewsItem]:
        headers = {}
        if HEADER_ETAG in self._validators:
            headers["If-None-Match"] = self._validators[HEADER_ETAG]
        if HEADER_LAST_MODIFIED in self._validators:
            headers["If-Modified-Since"] = self._validators[HEADER_LAST_MODIFIED]
        resp = self.session.get(self.url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        if resp.status_code == NOT_MODIFIED:
            return []
        resp.raise_for_status()
        self._remember(resp.headers)
        return parse_feed(resp.text, self.name)

    def _remember(self, headers) -> None:
        for name in (HEADER_ETAG, HEADER_LAST_MODIFIED):
            if headers.get(name):
                self._validators[name] = headers[name]
        match = MAX_AGE_PATTERN.search(headers.get(HEADER_CACHE_CONTROL, ""))
        self._max_age = float(match.group(1)) if match else 0.0
