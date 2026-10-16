"""Who an item is (story A19, scope 5): one canonical URL is one item, whichever feed lists it; a changed title,
summary or published time is a new version of it; a normalised headline links the same story told by another
publisher, without merging the two."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PREFIXES = ("utm_",)
TRACKING_NAMES = frozenset({"fbclid", "gclid", "ocid", "cmpid", "from", "ref", "source"})
FIELD_SEPARATOR = "\x1f"
NOT_WORD = re.compile(r"[\W_]+", re.UNICODE)


def canonical_url(url: str) -> str:
    """Lower-case scheme and host, no fragment, no tracking parameters, other parameters kept in order of name (an
    RBI release is `?prid=63818`: its id), no trailing slash on a path."""
    parts = urlsplit(url.strip())
    query = sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not _tracking(k))
    path = parts.path.rstrip("/") if parts.path not in ("", "/") else ""
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def item_id(url: str) -> str:
    return _sha256(canonical_url(url))


def version_of(title: str, summary: str, published_raw: str) -> str:
    return _sha256(FIELD_SEPARATOR.join((title, summary, published_raw)))


def headline_key(title: str) -> str:
    """Case-folded, punctuation and spaces collapsed: "RBI keeps repo rate at 5.5%" == "rbi keeps repo-rate at 5.5"."""
    return " ".join(NOT_WORD.sub(" ", title.casefold()).split())


def _tracking(name: str) -> bool:
    lowered = name.lower()
    return lowered.startswith(TRACKING_PREFIXES) or lowered in TRACKING_NAMES


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
