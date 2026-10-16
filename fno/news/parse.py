"""RSS 2.0 answers to items (story A19, scope 3). A web page, broken XML or a feed without items is a named
failure (`FeedProblem`), never "nothing new". Python's bundled expat refuses entity-expansion bombs and
ElementTree resolves no external entity, so a hostile feed cannot read files or exhaust memory."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from urllib.parse import urlsplit

from .identity import canonical_url
from .names import NO_ITEMS, NOT_XML
from .settings import Feed
from .times import TIME_FORMATS, PublishedTime

WEB_PAGE_STARTS = (b"<!doctype html", b"<html")
TAG = re.compile(r"<[^>]+>")


class FeedProblem(Exception):
    def __init__(self, kind: str, detail: str):
        super().__init__(detail)
        self.kind = kind


@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str
    summary: str
    published: PublishedTime


def parse_feed(data: bytes, feed: Feed) -> list[NewsItem]:
    """The feed's items, minus those under its excluded paths (SEBI's circulars are A20b's)."""
    if data.lstrip()[:20].lower().startswith(WEB_PAGE_STARTS):
        raise FeedProblem(NOT_XML, "the answer is a web page, not a feed")
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as exc:
        raise FeedProblem(NOT_XML, f"the answer is not XML ({type(exc).__name__})") from exc
    items = [_item(node, feed) for node in root.iter("item")]
    items = [item for item in items if item is not None]
    if not items:
        raise FeedProblem(NO_ITEMS, "the feed lists no items")
    return [item for item in items if not _excluded(item.url, feed.excluded_paths)]


def _item(node, feed: Feed) -> NewsItem | None:
    link = _text(node, "link") or _text(node, "guid")
    if not link.startswith(("https://", "http://")) or not _well_formed(link):
        return None  # an item without a usable link has no identity; skipped, never a crash of the whole run
    published = TIME_FORMATS[feed.time_format].read(_text(node, "pubDate"))
    return NewsItem(_plain(_text(node, "title")), link, _plain(_text(node, "description")), published)


def _text(node, tag: str) -> str:
    return (node.findtext(tag) or "").strip()


def _plain(text: str) -> str:
    return " ".join(html.unescape(TAG.sub(" ", html.unescape(text))).split())


def _well_formed(link: str) -> bool:
    try:
        canonical_url(link)
    except ValueError:  # e.g. "http://[abc/x": urlsplit refuses it
        return False
    return True


def _excluded(url: str, paths: tuple[str, ...]) -> bool:
    path = urlsplit(canonical_url(url)).path
    return any(path.startswith(prefix) for prefix in paths)
